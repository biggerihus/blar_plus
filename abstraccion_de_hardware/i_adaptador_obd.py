# abc (Abstract Base Classes) Este fragmento de código define una interfaz abstracta en Python utilizando el módulo nativo abc
# @abstractmethod Significa que cualquier clase que herede de IAdaptadorOBD tendrá que implementar ese método.

from abc import ABC, abstractmethod


class IAdaptadorOBD(ABC):
    """
    Interfaz abstracta para adaptadores OBD (On-Board Diagnostics).
    define los métodos que deben implementarse en cualquier clase concreta que actúe como adaptador OBD.
    """

    @abstractmethod
    def conectar(self, puerto: str, baudrate: int = 38400) -> bool:
        """
        Establece la conexión con el dispositivo OBD-II.

        Args:
            puerto: Puerto serie del dispositivo.
            baudrate: Velocidad de comunicación.

        Returns:
            True si la conexión fue exitosa.
        """
        raise NotImplementedError

    @abstractmethod
    def desconectar(self) -> None:
        """
        Cierra la conexión con el dispositivo OBD-II.
        """
        raise NotImplementedError

    @abstractmethod
    def leer_dtc(self) -> list[str]:
        """
        Obtiene los códigos de diagnóstico almacenados en la ECU.

        Returns:
            Lista de códigos DTC, por ejemplo ['P0300', 'P0171'].
        """
        raise NotImplementedError

    @abstractmethod
    def limpiar_dtc(self) -> bool:
        """
        Solicita borrar los códigos de diagnóstico de la ECU.

        Returns:
            True si la operación fue aceptada correctamente.
        """
        raise NotImplementedError

    @abstractmethod
    def leer_pid(self, pid: str) -> float:
        """
        Obtiene el valor numérico de un parámetro del vehículo.

        Args:
            pid: Identificador del parámetro OBD-II.

        Returns:
            Valor numérico del sensor.
        """
        raise NotImplementedError
