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
    Incluye protecciones de tiempo de espera, autodetección de baudrate,
    activación de líneas DTR/RTS para USB-CDC, liberación inmediata del descriptor
    del kernel Linux y caché de sensores no soportados.
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

    def __init__(self, timeout: float = 1.0) -> None:
        self.timeout = timeout
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

    def conectar(self, puerto: str = "/dev/ttyUSB0", baudrate: int = 38400) -> bool:
        """
        Establece conexión rápida con el ELM327 (priorizando 115200 baudios en ttyACM),
        prueba primero bus CAN estándar (ATSP6) y recurre a detección automática (ATSP0).
        """
        self.desconectar()
        self._pids_no_soportados.clear()
        self._registrar_log(f"=== Iniciando conexión en puerto {puerto} ===")

        if "ACM" in puerto.upper():
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
                self._registrar_log(f"Probando {puerto} a {vel} baudios...")
                ser = serial.Serial(
                    port=puerto,
                    baudrate=vel,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    write_timeout=0.4,
                    rtscts=False,
                    dsrdtr=False,
                    xonxoff=False,
                )
                # Afirmar DTR/RTS explícitamente para despertar interfaces USB-CDC
                try:
                    ser.dtr = True
                    ser.rts = True
                except Exception:
                    pass

                with self._io_lock:
                    self._serial = ser

                time.sleep(0.2)
                ser.reset_input_buffer()

                # Reinicio del chip ELM327 (read_until('>') espera hasta que termina el arranque)
                self._command("ATZ", timeout_override=1.5)
                time.sleep(0.15)
                ser.reset_input_buffer()

                # Configuración base del formato de tramas
                for command in ("ATE0", "ATL0", "ATS0", "ATH0"):
                    response = self._command(command, timeout_override=0.6)
                    if "?" in response:
                        raise RuntimeError(f"El ELM327 rechazó el comando {command}: {response}")

                # El chip ya respondió a esta velocidad; no volver a probar otro baudrate
                chip_detectado = True

                # Activar temporización adaptativa agresiva para reducir tiempos muertos
                try:
                    self._command("ATAT2", timeout_override=0.5)
                except Exception:
                    pass

                voltaje = self._leer_voltaje_obd()
                if voltaje is not None:
                    self._registrar_log(f"Voltaje leído en puerto OBD-II: {voltaje:.1f} V")

                # 1. Prueba rápida en CAN 11-bit 500 kbps (ATSP6, estándar en autos >= 2008)
                resp_bus = ""
                try:
                    self._command("ATSP6", timeout_override=0.5)
                    resp_bus = self._command("0100", timeout_override=1.2)
                except RuntimeError:
                    # 2. Respaldo automático para protocolos legacy (ISO 9141, KWP2000, J1850)
                    self._registrar_log("CAN rápido sin enlace; buscando protocolo automático (ATSP0)...")
                    self._command("ATSP0", timeout_override=0.5)
                    try:
                        resp_bus = self._command("0100", timeout_override=3.5)
                    except RuntimeError as err_bus:
                        if voltaje is not None and voltaje < 5.0:
                            raise RuntimeError(
                                f"Escáner detectado en {puerto}, pero sin conexión al vehículo "
                                f"(voltaje OBD-II: {voltaje:.1f} V). Conecte el cable al auto y ponga la llave en ON."
                            ) from err_bus
                        raise

                self._registrar_log(f"Respuesta inicial ECU (0100): {resp_bus}")

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
                if "Write timeout" in str(err) or "puerto USB" in str(err):
                    puerto_bloqueado = True
                self.desconectar()
                if chip_detectado or puerto_bloqueado:
                    break

        if ultimo_error is not None:
            raise ultimo_error
        return False

    @staticmethod
    def _cerrar_descriptor_seguro(ser: serial.Serial) -> None:
        """Cierra el descriptor serial en segundo plano sin detener el flujo principal."""
        try:
            if ser.is_open:
                ser.close()
        except Exception:
            pass

    def desconectar(self) -> None:
        """Descarta búferes del kernel Linux y libera el puerto serial de forma inmediata."""
        ser = self._serial
        self._serial = None
        if ser is not None:
            try:
                if hasattr(ser, "cancel_read"):
                    ser.cancel_read()
                if hasattr(ser, "cancel_write"):
                    ser.cancel_write()
                if ser.is_open:
                    # Vaciar cola de salida del kernel evita el closing_wait de 30 s en Linux
                    try:
                        fd = ser.fileno()
                        if termios is not None:
                            termios.tcflush(fd, termios.TCIOFLUSH)
                        os.set_blocking(fd, False)
                    except Exception:
                        pass
                    threading.Thread(
                        target=self._cerrar_descriptor_seguro,
                        args=(ser,),
                        daemon=True,
                    ).start()
                self._registrar_log("Puerto serial liberado correctamente.")
            except Exception as err:
                self._registrar_log(f"Aviso al cerrar puerto serial: {err}")

    def _command(self, command: str, timeout_override: Optional[float] = None) -> str:
        """Envía un comando ASCII al ELM327 y valida la integridad de la respuesta."""
        with self._io_lock:
            ser = self._serial
            if ser is None or not ser.is_open:
                raise RuntimeError("El adaptador ELM327 no está conectado.")

            timeout_original = ser.timeout
            try:
                if timeout_override is not None:
                    ser.timeout = timeout_override

                ser.reset_input_buffer()
                ser.write((command.strip() + "\r").encode("ascii"))
                raw = ser.read_until(b">")
            except serial.SerialTimeoutException as err:
                self.desconectar()
                raise RuntimeError(
                    "El puerto USB del escáner no responde (Write timeout). "
                    "Desconecte y vuelva a conectar el cable USB o verifique que otro servicio no lo esté ocupando."
                ) from err
            except serial.SerialException as err:
                self.desconectar()
                raise RuntimeError(f"Se perdió la comunicación USB con el escáner ELM327: {err}")
            finally:
                if timeout_override is not None and ser.is_open:
                    try:
                        ser.timeout = timeout_original
                    except Exception:
                        pass

        # Si el puerto fue cerrado mientras se leía, salir sin lanzar falso error de bus
        if self._serial is None:
            raise RuntimeError("Conexión cerrada por el usuario.")

        response = raw.decode("ascii", errors="ignore").replace(">", " ")
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
            response = self._command("03", timeout_override=2.0)
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
