"""
Adaptador simulador para pruebas del sistema Blar Plus.

Simula un dispositivo OBD-II de forma autónoma (sin requerir controles extra en la GUI),
incluyendo 5 códigos DTC en todos los niveles del semáforo (Alta, Media, Baja),
físicas correlacionadas de 10 sensores y ciclo completo de fallas físicas.

Autor: Mendivil Jimenez Jose Luis
Capa: Abstracción de Hardware (HAL) / Capa 4
"""

# Importación del módulo math para operaciones trigonométricas (sensor O2)
import math
# Importación del módulo random para la generación de ruido blanco en telemetría
import random
# Importación del módulo time para la sincronización temporal del delta-time
import time
# Importación de estructuras de tipado estricto
from typing import Dict, List, Optional

# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase AdaptadorSimulador que implementa el contrato de hardware IAdaptadorOBD
class AdaptadorSimulador(IAdaptadorOBD):
    """
    Simulador OBD-II autónomo para demostración completa del sistema y físicas correlacionadas.
    """

    # Catálogo base de 5 códigos DTC representativos de los 3 niveles del semáforo:
    # P0300 (Alta / Rojo), P0171 (Media / Amarillo), P0420 (Media / Amarillo),
    # P0442 (Baja / Verde), U0100 (Alta / Rojo)
    DTCS_POR_DEFECTO: List[str] = ["P0300", "P0171", "P0420", "P0442", "U0100"]

    # Constructor principal e inicialización de estados físicos y de control
    def __init__(self) -> None:
        """Inicializa el estado lógico, catálogo de 5 DTCs y variables del motor."""
        # Estado booleano de la conexión lógica con el adaptador
        self.conectado: bool = False
        # Lista activa de códigos de falla (DTC) simulados almacenados en la ECU
        self._dtcs_simulados: list[str] = list(self.DTCS_POR_DEFECTO)

        # Bandera de control para activar la secuencia autónoma de fallas físicas
        self.modo_secuencia_fallos: bool = True
        # Bandera opcional para simular rechazo de borrado por parte de la ECU (7F 04 22)
        self.simular_rechazo_borrado: bool = False
        # Contador del número de intentos de conexión ejecutados por el usuario
        self.intentos_conexion: int = 0
        # Límite de tiempo en segundos para demostrar la desconexión física en caliente (60s)
        self.tiempo_limite_sesion: float = 60.0

        # Definición del escenario de simulación activo
        self.modo_escenario: str = "NORMAL"
        # Tiempo acumulado total en segundos de la simulación
        self.tiempo_simulado: float = 0.0
        # Captura del timestamp inicial para cálculo de delta-time (dt)
        self._ultimo_timestamp: float = time.time()

        # Declaración de variables físicas correlacionadas del motor
        self.rpm: float = 850.0                       # Revoluciones por minuto
        self.velocidad: float = 0.0                   # Velocidad del vehículo en km/h
        self.temperatura_refrigerante: float = 45.0   # Temperatura del refrigerante en °C
        self.posicion_acelerador: float = 0.0         # Porcentaje de apertura de la mariposa
        self.carga_motor: float = 18.0                # Porcentaje de carga calculada del motor
        self.maf: float = 3.2                         # Flujo de masa de aire en g/s
        self.sensor_o2: float = 0.45                  # Voltaje del sensor de oxígeno en Voltios
        self.iat: float = 28.0                        # Temperatura del aire de admisión en °C
        self.nivel_combustible: float = 82.0          # Nivel del tanque de combustible en %
        self.presion_map: float = 34.0                # Presión absoluta del múltiple en kPa

        # Estado actual dentro de la máquina de estados de conducción
        self.estado_manejo: str = "RALENTI"
        # Temporizador interno para el control de transiciones de estados de manejo
        self._timer_estado: float = 0.0

    def restaurar_dtcs(self) -> None:
        """Restaura los 5 códigos DTC representativos en la memoria de la ECU simulada."""
        self._dtcs_simulados = list(self.DTCS_POR_DEFECTO)

    # Método de establecimiento de enlace con el puerto OBD-II
    def conectar(self, puerto: str = "SIMULADOR", baudrate: int = 38400) -> bool:
        """
        Simula la conexión al adaptador OBD-II evaluando la secuencia autónoma de demostración:
        - 1.er intento (con modo_secuencia_fallos=True): Rechaza enlace (simula cable no detectado).
        - 2.º intento en adelante: Enlaza con éxito y restaura los 5 DTCs si estaban vacíos.
        """
        time.sleep(0.1)
        self.intentos_conexion += 1

        # ESCENARIO 1: Rechazo del primer intento de conexión (Simulación de cable no detectado)
        if self.modo_secuencia_fallos and self.intentos_conexion == 1:
            self.conectado = False
            return False

        # Restaurar los 5 DTCs si fueron borrados en una sesión anterior
        if not self._dtcs_simulados:
            self.restaurar_dtcs()

        # ESCENARIO 2: Conexión exitosa
        self.conectado = True
        self._ultimo_timestamp = time.time()
        self.tiempo_simulado = 0.0
        self._timer_estado = 0.0
        self.estado_manejo = "RALENTI"
        return True

    # Método de desconexión del adaptador
    def desconectar(self) -> None:
        """Cierra la conexión lógica con el adaptador simulado."""
        self.conectado = False

    # Método privado de verificación de integridad del enlace físico
    def _verificar_estado_hardware(self) -> None:
        """Evalúa si la conexión se mantiene o si ocurrió una desconexión física en caliente."""
        if not self.conectado:
            raise RuntimeError("El adaptador OBD-II no está conectado al vehículo.")

        # En el 2.º intento dispara desconexión en caliente al cumplir tiempo_limite_sesion;
        # a partir del 3.er intento opera continuamente sin interrupciones.
        if (
            self.modo_secuencia_fallos
            and self.intentos_conexion == 2
            and self.tiempo_simulado >= self.tiempo_limite_sesion
        ):
            self.conectado = False
            raise RuntimeError(
                "El cable OBD-II se ha desconectado físicamente del puerto del vehículo."
            )

    # Método privado para la actualización matemática de las variables físicas correlacionadas
    def _actualizar_fisica(self) -> None:
        """Calcula las ecuaciones físicas interrelacionadas basadas en delta-time."""
        ahora = time.time()
        dt = ahora - self._ultimo_timestamp
        if dt <= 0:
            return
        # Limitar dt máximo para evitar saltos bruscos en las curvas
        dt = min(dt, 0.25)
        self._ultimo_timestamp = ahora

        self.tiempo_simulado += dt
        self._timer_estado += dt

        # MÁQUINA DE ESTADOS DE CONDUCCIÓN SUAVE Y CONTINUA
        if self.estado_manejo == "RALENTI":
            self.posicion_acelerador = max(2.0, self.posicion_acelerador - 10.0 * dt)
            self.velocidad = max(0.0, self.velocidad - 6.0 * dt)
            self.rpm = 820.0 + random.uniform(-12.0, 12.0)
            if self._timer_estado > 5.0:
                self.estado_manejo = "ACELERANDO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "ACELERANDO":
            self.posicion_acelerador = min(65.0, self.posicion_acelerador + 14.0 * dt)
            self.velocidad = min(95.0, self.velocidad + 11.0 * dt)
            self.rpm = 850.0 + (self.velocidad * 26.0) + random.uniform(-18.0, 18.0)
            if self.velocidad >= 95.0 or self._timer_estado > 9.0:
                self.estado_manejo = "CRUCERO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "CRUCERO":
            self.posicion_acelerador = 28.0 + random.uniform(-2.0, 2.0)
            self.velocidad = 95.0 + random.uniform(-1.5, 1.5)
            self.rpm = 2450.0 + random.uniform(-15.0, 15.0)
            if self._timer_estado > 10.0:
                self.estado_manejo = "DESACELERANDO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "DESACELERANDO":
            self.posicion_acelerador = 2.0
            self.velocidad = max(0.0, self.velocidad - 14.0 * dt)
            self.rpm = max(820.0, 820.0 + (self.velocidad * 18.0))
            if self.velocidad <= 0.0:
                self.estado_manejo = "RALENTI"
                self._timer_estado = 0.0

        # MODELADO TÉRMICO Y CORRELACIÓN DE SENSORES SECUNDARIOS
        if self.temperatura_refrigerante < 90.0:
            self.temperatura_refrigerante += 1.2 * dt
        else:
            self.temperatura_refrigerante = 90.0 + random.uniform(-0.5, 0.5)

        self.carga_motor = max(12.0, min(98.0, 14.0 + (self.posicion_acelerador * 0.85)))
        self.maf = max(2.0, (self.rpm / 1000.0) * (1.0 + (self.posicion_acelerador / 22.0)) * 4.2)
        self.presion_map = max(28.0, min(105.0, 32.0 + (self.carga_motor * 0.68)))
        self.iat = max(22.0, min(58.0, 26.0 + (self.temperatura_refrigerante * 0.14)))
        self.sensor_o2 = max(0.1, min(0.9, 0.5 + 0.38 * math.sin(2 * math.pi * self.tiempo_simulado * 0.5)))
        self.nivel_combustible = max(5.0, self.nivel_combustible - (0.0005 * dt))

    # Método para obtener la identificación del vehículo desde la ECU (Modo 09 OBD-II)
    def obtener_info_vehiculo(self) -> Dict[str, str]:
        """Devuelve los metadatos del vehículo simulado."""
        self._verificar_estado_hardware()
        return {
            "vehiculo": "Toyota Corolla 2.0L i-FORCE (Simulado)",
            "vin": "SIM-BLAR-2026-OK",
            "protocolo": "CAN Bus (ISO 15765-4 500kbps)",
        }

    # Método para leer la lista de códigos DTC activos de la memoria de la ECU
    def leer_dtc(self) -> list[str]:
        """Devuelve una copia de la lista de los códigos DTC activos."""
        self._verificar_estado_hardware()
        self._actualizar_fisica()
        return self._dtcs_simulados.copy()

    # Método para ejecutar la orden de borrado de códigos DTC en la ECU
    def limpiar_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """Ejecuta el borrado parcial o total de los códigos DTC."""
        self._verificar_estado_hardware()

        if self.simular_rechazo_borrado:
            return False

        if codigos:
            self._dtcs_simulados = [dtc for dtc in self._dtcs_simulados if dtc not in codigos]
        else:
            self._dtcs_simulados = []
        return True

    # Método para la consulta de PIDs específicos OBD-II
    def leer_pid(self, pid: str) -> float:
        """Devuelve el valor numérico procesado para el PID OBD-II solicitado."""
        self._verificar_estado_hardware()
        self._actualizar_fisica()

        pids_map = {
            "010C": self.rpm,
            "010D": self.velocidad,
            "0105": self.temperatura_refrigerante,
            "0104": self.carga_motor,
            "0111": self.posicion_acelerador,
            "0110": self.maf,
            "0114": self.sensor_o2,
            "010F": self.iat,
            "012F": self.nivel_combustible,
            "010B": self.presion_map,
        }

        if pid in pids_map:
            return round(pids_map[pid], 2)
        raise ValueError(f"--Desde el simulador-- PID no soportado: {pid}")
