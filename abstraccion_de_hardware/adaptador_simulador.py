"""
Adaptador simulador para pruebas del sistema Blar Plus.
Permite simular un escáner OBD-II sin conectar un vehículo real.
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""

# Importacion del modulo random para generar numeros aleatorios que simulan lecturas de sensores
import random
# Importacion del modulo time para simular retardos de red y tiempo de respuesta en la conexion
import time

# Importacion de la interfaz abstracta IAdaptadorOBD para cumplir el contrato de hardware
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD

# Clase AdaptadorSimulador que hereda de IAdaptadorOBD para simular la ECU en entorno de desarrollo
class AdaptadorSimulador(IAdaptadorOBD):
    """
    Simula la conexión y lectura de datos de un vehículo mediante OBD-II.
    """

    # Constructor e inicializador de atributos del simulador
    def __init__(self) -> None:
        # Estado inicial del simulador configurado como desconectado
        self.conectado: bool = False
        # Lista privada de codigos de falla ficticios iniciales
        self._dtcs_simulados: list[str] = ['P0300', 'P0171', 'P0420']

    # Metodo para simular la conexion al puerto serie del adaptador
    def conectar(self, puerto: str = "SIMULADOR", baudrate: int = 38400) -> bool:
        """
        Simula la conexión a un dispositivo OBD-II.

        Args:
            puerto: Puerto serie del dispositivo.
            baudrate: Velocidad de comunicación.
        """
        # Simula el retardo temporal que toma establecer la comunicacion serie
        time.sleep(0.1)
        # Cambia la bandera de estado a conectado
        self.conectado = True
        # Devuelve True confirmando el exito de la conexion
        return True

    # Metodo para simular la desconexion del dispositivo
    def desconectar(self) -> None:
        """
        Simula la desconexión del dispositivo OBD-II.
        """
        # Cambia la bandera de estado a desconectado
        self.conectado = False

    # Metodo para simular la lectura de codigos DTC almacenados
    def leer_dtc(self) -> list[str]:
        """
        Simula la lectura de códigos de diagnóstico (DTC) del vehículo.
        Devuelve los códigos de falla simulados.
        Returns:
            Lista de códigos DTC simulados.
        """
        # Verificacion del estado de conexion antes de realizar la lectura
        if not self.conectado:
            # Lanzamiento de excepcion de ejecucion si el simulador no esta conectado
            raise RuntimeError("--Desde el simulador-- No conectado al dispositivo OBD-II.")
        # Retorno de una copia independiente de la lista de codigos simulados
        return self._dtcs_simulados.copy()

    # Metodo para simular el borrado de codigos DTC de la memoria de la ECU
    def limpiar_dtc(self) -> bool:
        """
        Simula la limpieza de códigos de diagnóstico (DTC) del vehículo.
        Devuelve True si la operación fue exitosa.
        Returns:
            True si los códigos DTC fueron "limpiados" correctamente.
        """
        # Verificacion del estado de conexion antes de borrar
        if not self.conectado:
            # Lanzamiento de excepcion si no existe conexion activa
            raise RuntimeError("--Desde el simulador-- No conectado al dispositivo OBD-II.")
        # Vaciado de la lista de codigos simulados para simular el borrado
        self._dtcs_simulados = []
        # Retorno de confirmacion exitosa
        return True

    # Metodo para simular la consulta de lecturas de sensores mediante su PID OBD-II
    def leer_pid(self, pid: str) -> float:
        """
        Simula la lectura de un parámetro del vehículo mediante su PID.
        Devuelve un valor aleatorio para el PID solicitado.

        Args:
            pid: Identificador del parámetro OBD-II.
        """
        # Verificacion previa del estado de conexion
        if not self.conectado:
            # Lanzamiento de excepcion si se intenta leer sin estar conectado
            raise RuntimeError("--Desde el simulador-- El dispositivo OBD-II no está conectado.")

        # Evaluacion del PID solicitado para revoluciones del motor
        if pid == "010C":
            # Retorno de valor aleatorio flotante entre 800.0 y 3000.0 RPM redondeado a 2 decimales
            return round(random.uniform(800.0, 3000.0), 2)

        # Evaluacion del PID solicitado para velocidad del vehiculo
        elif pid == "010D":
            # Retorno de valor aleatorio flotante entre 0.0 y 120.0 km/h redondeado a 2 decimales
            return round(random.uniform(0.0, 120.0), 2)

        # Caso por defecto si se solicita un PID no soportado
        else:
            # Lanzamiento de excepcion indicando que el PID no esta implementado en el simulador
            raise ValueError(f"--Desde el simulador-- PID no soportado: {pid}")
