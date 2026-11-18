"""
Modulo Adaptador ELM327
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""
# Este archivo permite que Python se comunique con un adaptador ELM327
# conectado al vehículo mediante un puerto USB. El adaptador ELM327 funciona como intermediario:
# Python -> Puerto USB -> ELM327 -> Computadora del vehículo (ECU)

from datetime import datetime
import os
from pathlib import Path
import re
import select
import threading
import time
from typing import Callable, Dict, Optional
import serial
from serial.tools import list_ports

try:
    import termios
except ImportError:
    termios = None  # Compatible con Windows

from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
from abstraccion_de_hardware.estrategias_protocolo import EstrategiasProtocolo


class AdaptadorELM327(IAdaptadorOBD):
    """
    Comunicación OBD-II real mediante comandos AT y modos SAE J1979.
    En Linux/POSIX utiliza E/S directa no bloqueante (os.open + select) para
    evitar bloqueos de control en interfaces USB-CDC (/dev/ttyACM*), purga bytes
    residuales iniciales, realiza barrido completo de protocolos (CAN, KWP2000,
    ISO 9141-2) y almacena en caché los sensores no soportados por la ECU.
    """

    # Mapa de decodificadores soportados para los 10 sensores del sistema
    DECODIFICADORES_PID: Dict[str, Callable[[str], float]] = {
        "010C": EstrategiasProtocolo.decodificar_rpm,
        "010D": EstrategiasProtocolo.decodificar_velocidad,
        "0105": EstrategiasProtocolo.decodificar_temperatura_refrigerante,
        "0104": EstrategiasProtocolo.decodificar_carga_motor,
        "0111": EstrategiasProtocolo.decodificar_posicion_acelerador,
        "0110": EstrategiasProtocolo.decodificar_maf,
        "0114": EstrategiasProtocolo.decodificar_sensor_o2,
        "010F": EstrategiasProtocolo.decodificar_iat,
        "012F": EstrategiasProtocolo.decodificar_nivel_combustible,
        "010B": EstrategiasProtocolo.decodificar_presion_map,
    }

    def __init__(self, timeout: float = 1.5) -> None:
        self.timeout = timeout
        # Descriptor POSIX directo para Linux/macOS (evita bloqueos de tcsetattr en cdc_acm)
        self._fd: Optional[int] = None
        self._puerto_activo: str = "/dev/ttyACM0"
        # Respaldo pyserial para Windows
        self._serial: Optional[serial.Serial] = None
        self._io_lock = threading.Lock()
        # Conjunto de PIDs que la ECU del vehículo actual declaró como no disponibles
        self._pids_no_soportados: set[str] = set()
        # Protocolo OBD-II detectado en el vehículo real
        self._protocolo_detectado: str = "ISO 15765-4 (CAN)"
        # Archivo de bitácora local para diagnóstico sin conexión a internet
        self._ruta_log = Path.home() / "blar_plus_obd.log"

    def _registrar_log(self, mensaje: str) -> None:
        """Guarda trazas de diagnóstico en ~/blar_plus_obd.log para revisión offline."""
        try:
            marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            with self._ruta_log.open("a", encoding="utf-8") as archivo:
                archivo.write(f"[{marca_tiempo}] {mensaje}\n")
        except Exception:
            pass

    @staticmethod
    def detectar_puertos() -> list[str]:
        """Identifica los puertos seriales USB reales disponibles."""
        puertos_validos = []
        for p in list_ports.comports():
            dev = p.device
            hwid = (p.hwid or "").upper()
            # Filtrar los puertos serie virtuales del kernel de Linux sin hardware USB real
            if dev.startswith("/dev/ttyS") and "USB" not in hwid:
                continue
            puertos_validos.append(dev)
        return puertos_validos

    def _esta_abierto(self) -> bool:
        """Indica si existe un canal de comunicación activo (POSIX fd o pyserial)."""
        if self._fd is not None:
            return True
        return self._serial is not None and self._serial.is_open

    def _vaciar_entrada_posix(self, fd: int) -> None:
        """Descarta bytes residuales en el descriptor POSIX sin bloquear."""
        while True:
            try:
                listos, _, _ = select.select([fd], [], [], 0.01)
                if not listos:
                    break
                datos = os.read(fd, 256)
                if not datos:
                    break
            except (BlockingIOError, InterruptedError):
                break
            except OSError:
                break

    def _escribir_posix(self, fd: int, payload: bytes, timeout_escritura: float = 1.5) -> None:
        """Escribe todos los bytes en modo no bloqueante respetando el timeout."""
        pendiente = payload
        limite = time.monotonic() + timeout_escritura
        while pendiente:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError("Write timeout")
            _, listos_w, _ = select.select([], [fd], [], restante)
            if not listos_w:
                raise TimeoutError("Write timeout")
            try:
                escritos = os.write(fd, pendiente)
                if escritos <= 0:
                    raise OSError("El puerto serial no aceptó datos.")
                pendiente = pendiente[escritos:]
            except (BlockingIOError, InterruptedError):
                continue

    def _leer_hasta_prompt_posix(self, fd: int, timeout_lectura: float) -> bytes:
        """Lee fragmentos desde el descriptor POSIX hasta recibir '>' o agotar el tiempo."""
        acumulado = bytearray()
        limite = time.monotonic() + timeout_lectura
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                break
            listos_r, _, _ = select.select([fd], [], [], restante)
            if not listos_r:
                break
            try:
                trozo = os.read(fd, 256)
                if not trozo:
                    break
                acumulado.extend(trozo)
                if b">" in acumulado:
                    break
            except (BlockingIOError, InterruptedError):
                continue
        return bytes(acumulado)

    def _abrir_canal_directo(self, puerto: str, baudrate: int) -> None:
        """
        Abre el dispositivo serial. En POSIX utiliza os.open directo con O_NONBLOCK
        (omitiendo peticiones de control tcsetattr/DTR que bloquean chips USB-CDC).
        """
        self._puerto_activo = puerto
        if os.name == "posix":
            fd = os.open(puerto, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            # Solo ajustar velocidad en adaptadores FTDI/CH340 (/dev/ttyUSB*); en ttyACM se omite
            if "USB" in puerto.upper() and termios is not None:
                try:
                    attrs = termios.tcgetattr(fd)
                    vel_const = getattr(termios, f"B{baudrate}", termios.B38400)
                    termios.cfsetispeed(attrs, vel_const)
                    termios.cfsetospeed(attrs, vel_const)
                    attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
                    attrs[3] &= ~(termios.ECHO | termios.ICANON | termios.ISIG)
                    termios.tcsetattr(fd, termios.TCSANOW, attrs)
                except Exception:
                    pass

            with self._io_lock:
                self._fd = fd

            # Enviar CR inicial para limpiar cualquier byte nulo (\x00) pendiente en el chip
            try:
                self._escribir_posix(fd, b"\r", timeout_escritura=1.0)
                time.sleep(0.15)
                self._vaciar_entrada_posix(fd)
            except Exception:
                self.desconectar()
                raise
        else:
            ser = serial.Serial(
                port=puerto,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                write_timeout=1.5,
            )
            with self._io_lock:
                self._serial = ser
            time.sleep(0.15)
            ser.reset_input_buffer()

    def _leer_voltaje_obd(self) -> Optional[float]:
        """Consulta el voltaje del conector OBD-II (pin 16) mediante ATRV."""
        try:
            resp = self._command("ATRV", timeout_override=0.6)
            coincidencia = re.search(r"(\d+(?:\.\d+)?)", resp)
            if coincidencia:
                return float(coincidencia.group(1))
        except Exception:
            pass
        return None

    def _negociar_protocolo_vehiculo(self, puerto: str, voltaje: Optional[float]) -> str:
        """
        Intenta enlazar con la ECU probando primero CAN 11-bit (ATSP6), luego
        KWP2000 Fast Init (ATSP5) y finalmente el barrido automático completo (ATSP0)
        con tiempo suficiente para inicialización lenta de 5 baudios (ISO 9141-2 / KWP).
        """
        # 1. Prueba rápida en CAN 11-bit 500 kbps (ATSP6)
        try:
            self._command("ATSP6", timeout_override=0.6)
            return self._command("0100", timeout_override=1.5)
        except (RuntimeError, LookupError):
            pass

        # 2. Prueba rápida en ISO 14230-4 KWP2000 Fast Init (ATSP5)
        try:
            self._registrar_log("CAN sin enlace; probando KWP2000 Fast Init (ATSP5)...")
            self._command("ATSP5", timeout_override=0.6)
            return self._command("0100", timeout_override=2.5)
        except (RuntimeError, LookupError):
            pass

        # 3. Barrido automático completo de todos los protocolos OBD-II (incluye 5-baud init)
        self._registrar_log("Iniciando barrido automático completo de protocolos (ATSP0)...")
        self._command("ATSP0", timeout_override=0.6)
        try:
            return self._command("0100", timeout_override=12.0)
        except LookupError:
            self._registrar_log("ECU respondió NO DATA a 0100; verificando enlace con Servicio 03...")
            try:
                return self._command("03", timeout_override=3.0)
            except LookupError:
                return "NO DATA (ECU activa sin códigos)"
        except RuntimeError as err_bus:
            if voltaje is not None and voltaje < 5.0:
                raise RuntimeError(
                    f"Escáner detectado en {puerto}, pero sin alimentación del vehículo "
                    f"(voltaje OBD-II: {voltaje:.1f} V). Conecte el cable al auto y ponga la llave en ON."
                ) from err_bus
            raise RuntimeError(
                "El escáner respondió correctamente, pero la ECU del vehículo no contestó "
                "a ningún protocolo estándar OBD-II (SAE J1979). Verifique la llave en ON."
            ) from err_bus

    def conectar(self, puerto: str = "/dev/ttyUSB0", baudrate: int = 38400) -> bool:
        """
        Establece conexión con el ELM327 y negocia el protocolo OBD-II disponible
        en el vehículo.
        """
        self.desconectar()
        self._pids_no_soportados.clear()
        self._registrar_log(f"=== Iniciando conexión en puerto {puerto} ===")

        if os.name == "posix" and "ACM" in puerto.upper():
            # En interfaces USB-CDC el bus USB negocia la velocidad nativamente
            velocidades_prueba = [115200]
        elif "ACM" in puerto.upper():
            velocidades_prueba = [115200, 38400]
        else:
            velocidades_prueba = [baudrate]
            if 115200 not in velocidades_prueba:
                velocidades_prueba.append(115200)

        ultimo_error: Optional[Exception] = None

        for vel in velocidades_prueba:
            chip_detectado = False
            puerto_bloqueado = False
            try:
                self._registrar_log(f"Abriendo {puerto} ({vel} baudios)...")
                self._abrir_canal_directo(puerto, vel)

                # Reinicio del chip ELM327
                self._command("ATZ", timeout_override=1.8)
                time.sleep(0.15)
                if self._fd is not None:
                    self._vaciar_entrada_posix(self._fd)
                elif self._serial is not None:
                    self._serial.reset_input_buffer()

                # Configuración base del formato de tramas
                for command in ("ATE0", "ATL0", "ATS0", "ATH0"):
                    response = self._command(command, timeout_override=0.6)
                    if "?" in response:
                        raise RuntimeError(f"El ELM327 rechazó el comando {command}: {response}")

                chip_detectado = True

                # Temporización adaptativa estándar (compatibilidad con ECUs ISO/KWP y CAN)
                try:
                    self._command("ATAT1", timeout_override=0.5)
                except Exception:
                    pass

                voltaje = self._leer_voltaje_obd()
                if voltaje is not None:
                    self._registrar_log(f"Voltaje leído en puerto OBD-II: {voltaje:.1f} V")

                resp_bus = self._negociar_protocolo_vehiculo(puerto, voltaje)
                self._registrar_log(f"Respuesta inicial ECU: {resp_bus}")

                try:
                    proto = self._command("ATDP", timeout_override=0.6)
                    if proto:
                        self._protocolo_detectado = proto
                        self._registrar_log(f"Protocolo activo detectado: {proto}")
                except Exception:
                    pass

                return True

            except Exception as err:
                self._registrar_log(f"Fallo a {vel} baudios: {err}")
                ultimo_error = err
                if "Write timeout" in str(err) or "puerto" in str(err).lower():
                    puerto_bloqueado = True
                self.desconectar()
                if chip_detectado or puerto_bloqueado:
                    break

        if ultimo_error is not None:
            raise ultimo_error
        return False

    @staticmethod
    def _cerrar_fd_en_segundo_plano(fd: int) -> None:
        """Cierra el descriptor POSIX en segundo plano sin bloquear el hilo principal."""
        try:
            os.close(fd)
        except Exception:
            pass

    def desconectar(self) -> None:
        """Libera el descriptor POSIX o el objeto pyserial sin bloquear la interfaz."""
        fd = self._fd
        self._fd = None
        if fd is not None:
            try:
                if termios is not None:
                    termios.tcflush(fd, termios.TCIOFLUSH)
            except Exception:
                pass
            threading.Thread(
                target=self._cerrar_fd_en_segundo_plano,
                args=(fd,),
                daemon=True,
            ).start()
            self._registrar_log("Descriptor serial POSIX liberado correctamente.")

        ser = self._serial
        self._serial = None
        if ser is not None:
            try:
                if ser.is_open:
                    ser.close()
                self._registrar_log("Puerto serial liberado correctamente.")
            except Exception as err:
                self._registrar_log(f"Aviso al cerrar puerto serial: {err}")

    def _command(self, command: str, timeout_override: Optional[float] = None) -> str:
        """Envía un comando ASCII al ELM327 y valida la integridad de la respuesta."""
        timeout_efectivo = timeout_override if timeout_override is not None else self.timeout
        payload = (command.strip() + "\r").encode("ascii")

        with self._io_lock:
            fd = self._fd
            ser = self._serial
            if fd is None and (ser is None or not ser.is_open):
                raise RuntimeError("El adaptador ELM327 no está conectado.")

            puerto_actual = self._puerto_activo
            try:
                # Breve pausa para respetar el tiempo de guarda de protocolos ISO/KWP y USB-CDC
                time.sleep(0.03)

                if fd is not None:
                    self._vaciar_entrada_posix(fd)
                    self._escribir_posix(fd, payload, timeout_escritura=1.5)
                    raw = self._leer_hasta_prompt_posix(fd, timeout_lectura=timeout_efectivo)

                    # Si expiró sin recibir '>', enviar '\r' para abortar el barrido del ELM327
                    if not raw.endswith(b">") and self._fd is not None:
                        try:
                            self._escribir_posix(fd, b"\r", timeout_escritura=0.5)
                            raw += self._leer_hasta_prompt_posix(fd, timeout_lectura=0.5)
                        except Exception:
                            pass
                else:
                    assert ser is not None
                    timeout_original = ser.timeout
                    try:
                        ser.timeout = timeout_efectivo
                        ser.reset_input_buffer()
                        ser.write(payload)
                        raw = ser.read_until(b">")
                        if not raw.endswith(b">") and ser.is_open:
                            try:
                                ser.write(b"\r")
                                ser.timeout = 0.5
                                raw += ser.read_until(b">")
                            except Exception:
                                pass
                    finally:
                        if ser.is_open:
                            ser.timeout = timeout_original

            except (TimeoutError, serial.SerialTimeoutException) as err:
                self.desconectar()
                raise RuntimeError(
                    f"El puerto USB del escáner ({puerto_actual}) no responde (Write timeout). "
                    "Desconecte el escáner del auto y de la laptop por 5 segundos para reiniciarlo."
                ) from err
            except (OSError, serial.SerialException) as err:
                self.desconectar()
                raise RuntimeError(f"Se perdió la comunicación USB con el escáner ELM327: {err}") from err

        # Si el puerto fue cerrado mientras se leía, salir sin lanzar falso error de bus
        if not self._esta_abierto():
            raise RuntimeError("Conexión cerrada por el usuario.")

        response = raw.decode("ascii", errors="ignore").replace("\x00", "").replace(">", " ")
        response = re.sub(r"[\r\n]", " ", response)
        # Eliminar mensajes informativos del ELM327 para no contaminar la decodificación hex
        response = re.sub(r"SEARCHING\.+", " ", response, flags=re.IGNORECASE)
        response = re.sub(r"BUS INIT:\s*(\.\.\.)?\s*OK", " ", response, flags=re.IGNORECASE)
        response = re.sub(r"\s+", " ", response).strip()
        resp_upper = response.upper()

        self._registrar_log(f"TX: {command}  |  RX: '{response}'")

        # Errores físicos de enlace o desconexión del vehículo
        if (
            not response
            or "UNABLE TO CONNECT" in resp_upper
            or "BUS ERROR" in resp_upper
            or "CAN ERROR" in resp_upper
            or "STOPPED" in resp_upper
        ):
            raise RuntimeError(
                f"Sin respuesta válida del vehículo para {command} (verifique llave en ON): {response}"
            )

        # Respuestas válidas del protocolo indicando que el sensor específico no existe en este auto
        if "NO DATA" in resp_upper or resp_upper.startswith("7F"):
            raise LookupError(f"Parámetro {command} no soportado por la ECU del vehículo.")

        return response

    def obtener_info_vehiculo(self) -> Dict[str, str]:
        """Devuelve la información del enlace real establecida con el vehículo."""
        return {
            "vehiculo": "Vehículo Real Conectado (OBD-II)",
            "vin": "Lectura Activa SAE J1979",
            "protocolo": self._protocolo_detectado,
        }

    def leer_dtc(self) -> list[str]:
        """Consulta los códigos de falla confirmados (Servicio 03)."""
        try:
            response = self._command("03", timeout_override=2.5)
            return EstrategiasProtocolo.decodificar_dtc_bytes(response)
        except LookupError:
            # Algunas ECUs responden NO DATA cuando no tienen códigos almacenados
            return []

    def limpiar_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """
        Envía el Servicio 04 OBD-II para borrar los códigos de diagnóstico de la ECU.
        Nota: Por estándar SAE J1979, el modo 04 borra todos los DTCs emitidos.
        """
        response = self._command("04", timeout_override=2.5).upper()
        return "44" in response or "OK" in response

    def leer_pid(self, pid: str) -> float:
        """
        Consulta un PID OBD-II y lo decodifica. Si el vehículo no cuenta con ese sensor,
        lo registra en caché y devuelve 0.0 sin interrumpir la sesión.
        """
        pid_norm = pid.upper().replace(" ", "")

        if pid_norm not in self.DECODIFICADORES_PID:
            raise ValueError(f"PID no soportado: {pid_norm}")

        if pid_norm in self._pids_no_soportados:
            return 0.0

        try:
            response = self._command(pid_norm)
            decodificador = self.DECODIFICADORES_PID[pid_norm]
            return decodificador(response)
        except LookupError:
            # Marcar el sensor como no equipado en este vehículo para no consultarlo más
            self._pids_no_soportados.add(pid_norm)
            return 0.0
