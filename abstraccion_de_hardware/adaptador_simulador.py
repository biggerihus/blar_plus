"""
Adaptador simulador para pruebas del sistema Blar Plus.

Simula un dispositivo OBD-II permitiendo validar escenarios de falla física
y correlación de física vehicular.

Autor: Mendivil Jimenez Jose Luis & Estrada Loaiza Rogelio
Capa: Abstracción de Hardware (HAL) / Capa 4
"""

# Importación del módulo math para operaciones trigonométricas (sensor O2)
import math
# Importación del módulo random para la generación de ruido blanco en telemetría
import random
# Importación del módulo time para la sincronización temporal del delta-time
import time
# Importación de estructuras de tipado estricto
from typing import Dict, Optional

# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase AdaptadorSimulador que implementa el contrato de hardware IAdaptadorOBD
class AdaptadorSimulador(IAdaptadorOBD):
    """
    Simulador OBD-II para validación de resiliencia del sistema y físicas correlacionadas.
    """

    # Constructor principal e inicialización de estados físicos y de control
    def __init__(self) -> None:
        # Estado booleano de la conexión lógica con el adaptador
        self.conectado: bool = False
        # Lista de códigos de falla (DTC) simulados almacenados en la ECU
        self._dtcs_simulados: list[str] = ['P0300', 'P0171', 'P0420']

        # Bandera de control para activar la secuencia de prueba de fallas físicas
        self.modo_secuencia_fallos: bool = True
        # Contador del número de intentos de conexión ejecutados por el usuario
        self.intentos_conexion: int = 0
        # Límite de tiempo en segundos para forzar la desconexión física del simulador (40 segundos)
        self.tiempo_limite_sesion: float = 40.0

        # Definición del escenario de simulación activo
        self.modo_escenario: str = "NORMAL"
        # Tiempo acumulado total en segundos de la simulación
        self.tiempo_simulado: float = 0.0
        # Captura del timestamp inicial para cálculo de delta-time (dt)
        self._ultimo_timestamp: float = time.time()

        # Declaración de variables físicas correlacionadas del motor
        self.rpm: float = 800.0                       # Revoluciones por minuto
        self.velocidad: float = 0.0                   # Velocidad del vehículo en km/h
        self.temperatura_refrigerante: float = 25.0   # Temperatura del refrigerante en °C
        self.posicion_acelerador: float = 0.0        # Porcentaje de apertura de la mariposa
        self.carga_motor: float = 15.0                # Porcentaje de carga calculada del motor
        self.maf: float = 2.5                         # Flujo de masa de aire en g/s
        self.sensor_o2: float = 0.45                  # Voltaje del sensor de oxígeno en Voltios
        self.iat: float = 25.0                        # Temperatura del aire de admisión en °C
        self.nivel_combustible: float = 85.0          # Nivel del tanque de combustible en %
        self.presion_map: float = 32.0                # Presión absoluta del múltiple en kPa

        # Estado actual dentro de la máquina de estados de conducción
        self.estado_manejo: str = "RALENTI"
        # Temporizador interno para el control de transiciones de estados de manejo
        self._timer_estado: float = 0.0

    # Método de establecimiento de enlace con el puerto OBD-II
    def conectar(self, puerto: str = "SIMULADOR", baudrate: int = 38400) -> bool:
        """
        Simula la conexión al adaptador OBD-II evaluando la secuencia de fallos programada.
        """
        # Simulación de retardo físico de inicialización del puerto serie
        time.sleep(0.1)
        # Incremento del contador global de intentos de conexión
        self.intentos_conexion += 1

        # ESCENARIO 1: Rechazo del primer intento de conexión (Simulación de cable no detectado)
        if self.modo_secuencia_fallos and self.intentos_conexion == 1:
            # Marcamos la conexión como fallida
            self.conectado = False
            # Retornamos False notificando la incapacidad de enlazar con el hardware
            return False

        # ESCENARIO 2: Aceptación del segundo intento en adelante (Conexión exitosa)
        self.conectado = True
        # Reiniciar timestamp del último ciclo para delta-time
        self._ultimo_timestamp = time.time()
        # Restablecer el contador de tiempo de simulación física
        self.tiempo_simulado = 0.0
        # Retornar True confirmando enlace exitoso
        return True

    # Método de desconexión del adaptador
    def desconectar(self) -> None:
        """Cierra la conexión lógica con el adaptador simulado."""
        # Desactivar la bandera de conexión
        self.conectado = False

    # Método privado de verificación de integridad del enlace físico
    def _verificar_estado_hardware(self) -> None:
        """Evalúa si la conexión se mantiene o si ocurrió una desconexión en caliente."""
        # Lanzar excepción si se intenta realizar una lectura en estado desconectado
        if not self.conectado:
            raise RuntimeError("El adaptador OBD-II no está conectado al vehículo.")

        # ESCENARIO 3: Forzar desconexión física si el tiempo excede el límite programado (40 segundos)
        if self.modo_secuencia_fallos and self.tiempo_simulado >= self.tiempo_limite_sesion:
            # Cambiar estado interno a desconectado
            self.conectado = False
            # Lanzar excepción pura de hardware (sin formato visual)
            raise RuntimeError("El cable OBD-II se ha desconectado físicamente del puerto del vehículo.")

    # Método privado para la actualización matemática de las variables físicas correlacionadas
    def _actualizar_fisica(self) -> None:
        """Calcula las ecuaciones físicas interrelacionadas basadas en delta-time."""
        # Obtención del tiempo actual en segundos
        ahora = time.time()
        # Cálculo del paso de tiempo transcurrido (delta-time)
        dt = ahora - self._ultimo_timestamp
        # Protección contra saltos temporales negativos o nulos
        if dt <= 0:
            return
        # Actualizar el último timestamp registrado
        self._ultimo_timestamp = ahora

        # Acumular el tiempo simulado total y del estado actual
        self.tiempo_simulado += dt
        self._timer_estado += dt

        # MÁQUINA DE ESTADOS DE CONDUCCIÓN
        if self.estado_manejo == "RALENTI":
            # Reducción paulatina de la posición del acelerador
            self.posicion_acelerador = max(0.0, self.posicion_acelerador - 10.0 * dt)
            # Reducción paulatina de la velocidad
            self.velocidad = max(0.0, self.velocidad - 5.0 * dt)
            # Oscilación de RPM en torno al ralentí estable (800 RPM)
            self.rpm = 800.0 + random.uniform(-10.0, 10.0)
            # Transición a estado ACELERANDO al superar los 8 segundos
            if self._timer_estado > 8.0:
                self.estado_manejo = "ACELERANDO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "ACELERANDO":
            # Incremento de la apertura del acelerador
            self.posicion_acelerador = min(65.0, self.posicion_acelerador + 15.0 * dt)
            # Incremento continuo de la velocidad
            self.velocidad = min(90.0, self.velocidad + 12.0 * dt)
            # RPM correlacionadas directamente con la velocidad
            self.rpm = 800.0 + (self.velocidad * 28.0) + random.uniform(-20.0, 20.0)
            # Transición a estado CRUCERO al alcanzar la velocidad objetivo
            if self.velocidad >= 90.0 or self._timer_estado > 10.0:
                self.estado_manejo = "CRUCERO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "CRUCERO":
            # Estabilización del acelerador en torno al 25%
            self.posicion_acelerador = 25.0 + random.uniform(-2.0, 2.0)
            # Mantener velocidad de crucero constante a 90 km/h
            self.velocidad = 90.0 + random.uniform(-1.5, 1.5)
            # Mantener RPM constantes a 2200 RPM
            self.rpm = 2200.0 + random.uniform(-15.0, 15.0)
            # Transición a estado DESACELERANDO tras 12 segundos
            if self._timer_estado > 12.0:
                self.estado_manejo = "DESACELERANDO"
                self._timer_estado = 0.0

        elif self.estado_manejo == "DESACELERANDO":
            # Mariposa de aceleración completamente cerrada
            self.posicion_acelerador = 0.0
            # Reducción progresiva de velocidad por freno motor
            self.velocidad = max(0.0, self.velocidad - 18.0 * dt)
            # Caída progresiva de RPM hasta el límite de ralentí
            self.rpm = max(800.0, 800.0 + (self.velocidad * 20.0))
            # Retorno a estado RALENTI al detener el vehículo
            if self.velocidad <= 0.0:
                self.estado_manejo = "RALENTI"
                self._timer_estado = 0.0

        # MODELADO TÉRMICO Y CORRELACIÓN DE SENSORES SECUNDARIOS
        if self.temperatura_refrigerante < 90.0:
            # Calentamiento progresivo del motor hasta temperatura de trabajo
            self.temperatura_refrigerante += 0.8 * dt
        else:
            # Fluctuación térmica estable a 90 °C
            self.temperatura_refrigerante = 90.0 + random.uniform(-0.5, 0.5)

        # Carga calculada proporcional al acelerador
        self.carga_motor = max(10.0, min(99.0, 12.0 + (self.posicion_acelerador * 0.8)))
        # Flujo MAF derivado de las RPM y la apertura del acelerador
        self.maf = max(1.5, (self.rpm / 1000.0) * (1.0 + (self.posicion_acelerador / 20.0)) * 4.2)
        # Presión MAP basada en la carga del motor
        self.presion_map = max(25.0, min(105.0, 30.0 + (self.carga_motor * 0.7)))
        # Temperatura IAT influenciada por la temperatura del motor
        self.iat = max(20.0, min(60.0, 25.0 + (self.temperatura_refrigerante * 0.15)))
        # Sensor de oxígeno (O2) - Oscilación senoidal natural a 0.5 Hz entre 0.1V y 0.9V
        self.sensor_o2 = max(0.1, min(0.9, 0.5 + 0.38 * math.sin(2 * math.pi * self.tiempo_simulado * 0.5)))
        # Consumo paulatino de combustible
        self.nivel_combustible = max(0.0, self.nivel_combustible - (0.0005 * dt))

    # Método para obtener la identificación del vehículo desde la ECU (Modo 09 OBD-II)
    def obtener_info_vehiculo(self) -> Dict[str, str]:
        """Devuelve los metadatos del vehículo tras validar la integridad física del enlace."""
        # Verificación preventiva del enlace de hardware
        self._verificar_estado_hardware()
        # Retorno del diccionario de metadatos del vehículo
        return {
            "vehiculo": "Toyota Corolla 2.0L i-FORCE (Simulado)",
            "vin": "4T1B11HK5LU987654",
            "protocolo": "CAN Bus (ISO 15765-4 500kbps)",
        }

    # Método para leer la lista de códigos DTC activos de la memoria de la ECU
    def leer_dtc(self) -> list[str]:
        """Devuelve una copia de la lista de códigos DTC activos."""
        # Verificación de conexión física
        self._verificar_estado_hardware()
        # Actualización de las ecuaciones de física vehicular
        self._actualizar_fisica()
        # Retorno de la lista de códigos DTC
        return self._dtcs_simulados.copy()

    # Método para ejecutar la orden de borrado de códigos DTC en la ECU
    def limpiar_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """Ejecuta el borrado parcial o total de los códigos DTC."""
        # Verificación de conexión física
        self._verificar_estado_hardware()
        # Eliminación de códigos seleccionados o vaciado completo
        if codigos:
            self._dtcs_simulados = [dtc for dtc in self._dtcs_simulados if dtc not in codigos]
        else:
            self._dtcs_simulados = []
        # Confirmación de borrado exitoso
        return True

    # Método para la consulta de PIDs específicos OBD-II
    def leer_pid(self, pid: str) -> float:
        """Devuelve el valor numérico procesado para el PID OBD-II solicitado."""
        # Verificación de la integridad de hardware
        self._verificar_estado_hardware()
        # Actualización del modelo físico
        self._actualizar_fisica()

        # Mapeo de PIDs a atributos de física
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

        # Retorno del valor redondeado si el PID es soportado
        if pid in pids_map:
            return round(pids_map[pid], 2)
        # Lanzar excepción en caso de PID no soportado
        raise ValueError(f"--Desde el simulador-- PID no soportado: {pid}")
