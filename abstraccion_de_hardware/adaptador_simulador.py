"""
Adaptador simulador para pruebas del sistema Blar Plus.
Permite simular un escáner OBD-II sin conectar un vehículo real.
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""

# Importacion de Optional para tipado flexible en argumentos de borrado
from typing import Optional
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
    def limpiar_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """
        Simula la limpieza de códigos de diagnóstico (DTC) del vehículo.
        Permite el borrado parcial (lista específica) o total (si codigos es None).

        Args:
            codigos (Optional[list[str]]): Lista opcional de códigos específicos a eliminar.

        Returns:
            True si los códigos DTC fueron eliminados correctamente.
        """
        # Verificacion del estado de conexion antes de borrar
        if not self.conectado:
            # Lanzamiento de excepcion si no existe conexion activa
            raise RuntimeError("--Desde el simulador-- No conectado al dispositivo OBD-II.")

        # Evaluar si se especificaron codigos concretos a eliminar
        if codigos:
            # Filtrado para conservar unicamente los codigos no seleccionados
            self._dtcs_simulados = [
                dtc for dtc in self._dtcs_simulados if dtc not in codigos
            ]
        else:
            # Vaciado total de la lista de codigos simulados
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

        # Evaluacion del PID solicitado para revoluciones del motor (RPM - PID 010C)
        if pid == "010C":
            return round(random.uniform(800.0, 3000.0), 2)

        # Evaluacion del PID solicitado para velocidad del vehiculo (km/h - PID 010D)
        elif pid == "010D":
            return round(random.uniform(0.0, 120.0), 2)

        # Evaluacion del PID solicitado para temperatura del refrigerante (°C - PID 0105)
        elif pid == "0105":
            return round(random.uniform(85.0, 105.0), 2)

        # Evaluacion del PID solicitado para porcentaje de carga del motor (% - PID 0104)
        elif pid == "0104":
            return round(random.uniform(15.0, 85.0), 2)

        # Evaluacion del PID solicitado para posicion del acelerador (% - PID 0111)
        elif pid == "0111":
            return round(random.uniform(0.0, 100.0), 2)

        # Evaluacion del PID solicitado para flujo de masa de aire MAF (g/s - PID 0110)
        elif pid == "0110":
            return round(random.uniform(2.0, 45.0), 2)

        # Evaluacion del PID solicitado para voltaje del sensor de oxigeno O2 (V - PID 0114)
        elif pid == "0114":
            return round(random.uniform(0.10, 0.90), 2)

        # Evaluacion del PID solicitado para temperatura del aire de admision IAT (°C - PID 010F)
        elif pid == "010F":
            return round(random.uniform(20.0, 45.0), 2)

        # Evaluacion del PID solicitado para nivel de combustible (% - PID 012F)
        elif pid == "012F":
            return round(random.uniform(25.0, 95.0), 2)

        # Evaluacion del PID solicitado para presion absoluta del multiple MAP (kPa - PID 010B)
        elif pid == "010B":
            return round(random.uniform(30.0, 105.0), 2)

        # Caso por defecto si se solicita un PID no soportado
        else:
            # Lanzamiento de excepcion indicando que el PID no esta implementado en el simulador
            raise ValueError(f"--Desde el simulador-- PID no soportado: {pid}")
