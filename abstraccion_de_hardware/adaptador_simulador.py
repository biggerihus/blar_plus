
"""
Adaptador simulador para pruebas del sistema Blar Plus.
Permite simular un escáner OBD-II sin conectar un vehículo real.
"""

import random  #genera números aleatorios para simular los sensores.
import time    #permite simular el pequeño retraso de conexión.


# Importamos nuestra interfaz abstracta, creada en el módulo i_adaptador_obd.
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD

# AdaptadorSimulador hereda de IAdaptadorOBD.
class AdaptadorSimulador(IAdaptadorOBD):
    """
        Simula la conexión y lectura de datos de un vehículo mediante OBD-II.
    """

    # constructor
    def __init__(self) -> None:
        # Cuando creamos el simulador, comienza desconectado.
        self.conectado: bool = False

        # tres codigos de falla ficticios.
        self._dtcs_simulados: list[str] = ['P0300', 'P0171', 'P0420']


    def conectar(self, puerto: str, baudrate: int = 38400) -> bool:
        """
        Simula la conexión a un dispositivo OBD-II.

        Args:
            puerto: Puerto serie del dispositivo.
            baudrate: Velocidad de comunicación.
        """
        time.sleep(0.1)  # Simula tiempo de conexión
        self.conectado = True  # y cambiamos el estado de conexión.
        return True  # Devuelve True para indicar que la conexión fue exitosa.

    def desconectar(self) -> None:
        """
        Simula la desconexión del dispositivo OBD-II.
        """
        self.conectado = False

    def leer_dtc(self) -> list[str]:
        """
        Simula la lectura de códigos de diagnóstico (DTC) del vehículo.
        Devuelve los códigos de falla simulados.
        Returns:
            Lista de códigos DTC simulados.
        """
        
        if not self.conectado:
            raise RuntimeError("--Desde el simulador-- No conectado al dispositivo OBD-II.")
        return self._dtcs_simulados.copy()

    def limpiar_dtc(self) -> bool:
        """
        Simula la limpieza de códigos de diagnóstico (DTC) del vehículo.
        Devuelve True si la operación fue exitosa.
        Returns:
            True si los códigos DTC fueron "limpiados" correctamente.
        """
        if not self.conectado:
            raise RuntimeError("--Desde el simulador-- No conectado al dispositivo OBD-II.")
        self._dtcs_simulados = []  # Limpia los códigos de falla simulados
        return True


    def leer_pid(self, pid: str) -> float:
        """
        Simula la lectura de un parámetro del vehículo mediante su PID.
        Devuelve un valor aleatorio para el PID solicitado.

        Args:
            pid: Identificador del parámetro OBD-II.
        """
        if not self.conectado:
            raise RuntimeError("--Desde el simulador-- El dispositivo OBD-II no está conectado.")

        if pid == "010C":  # RPM del motor
            return round(random.uniform(800.0 , 3000.0), 2) # devuelve un valor aleatorio entre 800 y 3000 RPM
        
        elif pid == "010D":  # Velocidad del vehículo
            return round(random.uniform(0.0, 120.0), 2)  # devuelve un valor aleatorio entre 0 y 120 km/h

        else:
            raise ValueError(f"--Desde el simulador-- PID no soportado: {pid}")

        
        
    
    