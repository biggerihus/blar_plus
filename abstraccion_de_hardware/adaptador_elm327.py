"""
Modulo Adaptador ELM327
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""
# Este archivo permite que Python se comunique con un adaptador ELM327
# conectado al vehículo mediante un puerto USB. El adaptador ELM327 funciona como intermediario:
# Python -> Puerto USB -> ELM327 -> Computadora del vehículo (ECU)

import re
import time
from typing import Callable, Dict, Optional
import serial
from serial.tools import list_ports

from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
from abstraccion_de_hardware.estrategias_protocolo import EstrategiasProtocolo


class AdaptadorELM327(IAdaptadorOBD):
    """
    Comunicación OBD-II real mediante comandos AT y modos SAE J1979.
    Incluye protecciones de tiempo de espera, autodetección de baudrate
    y caché de sensores no soportados para evitar saturar la ECU del vehículo.
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
        self._serial: Optional[serial.Serial] = None
        # Conjunto de PIDs que la ECU del vehículo actual declaró como no disponibles
        self._pids_no_soportados: set[str] = set()
        # Protocolo OBD-II detectado en el vehículo real
        self._protocolo_detectado: str = "ISO 15765-4 (CAN)"

    @staticmethod
    def detectar_puertos() -> list[str]:
        """Identifica los puertos seriales USB reales disponibles."""
        puertos_validos = []
        for p in list_ports.comports():
            dev = p.device
            # Filtrar los puertos serie virtuales del kernel de Linux sin hardware USB real
            if dev.startswith("/dev/ttyS") and "USB" not in p.hwid.upper():
                continue
            puertos_validos.append(dev)
        return puertos_validos

    def conectar(self, puerto: str = "/dev/ttyUSB0", baudrate: int = 38400) -> bool:
        """
        Establece conexión con el ELM327 probando la velocidad indicada y,
        en caso necesario, 115200 baudios (estándar en adaptadores USB modernos).
        """
        self.desconectar()
        self._pids_no_soportados.clear()

        velocidades_prueba = [baudrate]
        if 115200 not in velocidades_prueba:
            velocidades_prueba.append(115200)

        ultimo_error: Optional[Exception] = None

        for vel in velocidades_prueba:
            try:
                self._serial = serial.Serial(
                    puerto,
                    baudrate=vel,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                )
                time.sleep(0.8)
                self._serial.reset_input_buffer()

                for command in ("ATZ", "ATE0", "ATL0", "ATS0", "ATH0", "ATSP0"):
                    response = self._command(command)
                    if "?" in response:
                        raise RuntimeError(f"El ELM327 rechazó el comando {command}: {response}")

                # Consultar protocolo activo asignado automáticamente por el chip
                try:
                    proto = self._command("ATDP")
                    if proto:
                        self._protocolo_detectado = proto
                except Exception:
                    pass

                return True

            except Exception as err:
                ultimo_error = err
                self.desconectar()

        if ultimo_error is not None:
            raise ultimo_error
        return False

    def desconectar(self) -> None:
        """Cierra de forma segura el puerto serial liberando el hardware."""
        if self._serial is not None:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except Exception:
                pass
            finally:
                self._serial = None

    def _command(self, command: str) -> str:
        """Envía un comando ASCII al ELM327 y valida la integridad de la respuesta."""
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("El adaptador ELM327 no está conectado.")

        try:
            self._serial.reset_input_buffer()
            self._serial.write((command.strip() + "\r").encode("ascii"))
            self._serial.flush()
            raw = self._serial.read_until(b">")
        except serial.SerialException as err:
            self.desconectar()
            raise RuntimeError(f"Se perdió la comunicación USB con el escáner ELM327: {err}")

        response = raw.decode("ascii", errors="ignore").replace(">", " ")
        response = re.sub(r"[\r\n]", " ", response)
        response = re.sub(r"\s+", " ", response).strip()
        resp_upper = response.upper()

        # Errores físicos de enlace o desconexión del vehículo
        if (
            not response
            or "UNABLE TO CONNECT" in resp_upper
            or "BUS ERROR" in resp_upper
            or "CAN ERROR" in resp_upper
        ):
            raise RuntimeError(f"Sin respuesta válida del vehículo para {command}: {response}")

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
            response = self._command("03")
            return EstrategiasProtocolo.decodificar_dtc_bytes(response)
        except LookupError:
            # Algunas ECUs responden NO DATA cuando no tienen códigos almacenados
            return []

    def limpiar_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """
        Envía el Servicio 04 OBD-II para borrar los códigos de diagnóstico de la ECU.
        Nota: Por estándar SAE J1979, el modo 04 borra todos los DTCs emitidos.
        """
        response = self._command("04").upper()
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
