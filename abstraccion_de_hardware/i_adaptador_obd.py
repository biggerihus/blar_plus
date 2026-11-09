"""
Modulo Interface Adaptador OBD
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""

# Importacion de ABC y abstractmethod del modulo nativo abc para definir clases e interfaces abstractas
from abc import ABC, abstractmethod

# Definicion de la clase base abstracta IAdaptadorOBD que sirve de contrato para los adaptadores OBD-II
class IAdaptadorOBD(ABC):
    """
    Interfaz abstracta para adaptadores OBD (On-Board Diagnostics).
    define los métodos que deben implementarse en cualquier clase concreta que actúe como adaptador OBD.
    """

    # Definicion del metodo abstracto para establecer conexion con el dispositivo
    @abstractmethod
    def conectar(self, puerto: str = "SIMULADOR", baudrate: int = 38400) -> bool:
        """
        Establece la conexión con el dispositivo OBD-II.

        Args:
            puerto: Puerto serie del dispositivo.
            baudrate: Velocidad de comunicación.

        Returns:
            True si la conexión fue exitosa.
        """
        # Excepcion lanzada si una subclase no implementa este metodo
        raise NotImplementedError

    # Definicion del metodo abstracto para cerrar la conexion
    @abstractmethod
    def desconectar(self) -> None:
        """
        Cierra la conexión con el dispositivo OBD-II.
        """
        # Excepcion lanzada si una subclase no implementa este metodo
        raise NotImplementedError

    # Definicion del metodo abstracto para consultar codigos de falla
    @abstractmethod
    def leer_dtc(self) -> list[str]:
        """
        Obtiene los códigos de diagnóstico almacenados en la ECU.

        Returns:
            Lista de códigos DTC, por ejemplo ['P0300', 'P0171'].
        """
        # Excepcion lanzada si una subclase no implementa este metodo
        raise NotImplementedError

    # Definicion del metodo abstracto para borrar codigos de falla
    @abstractmethod
    def limpiar_dtc(self) -> bool:
        """
        Solicita borrar los códigos de diagnóstico de la ECU.

        Returns:
            True si la operación fue aceptada correctamente.
        """
        # Excepcion lanzada si una subclase no implementa este metodo
        raise NotImplementedError

    # Definicion del metodo abstracto para consultar parametros/sensores
    @abstractmethod
    def leer_pid(self, pid: str) -> float:
        """
        Obtiene el valor numérico de un parámetro del vehículo.

        Args:
            pid: Identificador del parámetro OBD-II.

        Returns:
            Valor numérico del sensor.
        """
        # Excepcion lanzada si una subclase no implementa este metodo
        raise NotImplementedError
