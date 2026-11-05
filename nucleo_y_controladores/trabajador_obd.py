"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread).

Autor: Erick Polanco Romero
"""

from PySide6.QtCore import QThread, Signal
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para el sondeo y lectura de datos OBD-II.

    Evita el bloqueo de la interfaz gráfica (GUI Thread) ejecutando las
    operaciones de entrada/salida (puerto serie o red) en un hilo independiente.

    Atributos de Clase (Señales Qt):
        datos_recibidos (Signal): Emite una lista de cadenas con los códigos DTC leídos.
        error_ocurrido (Signal): Emite una cadena con el mensaje descriptivo del fallo.
    """

    # Señal Qt emitida al obtener exitosamente datos del vehículo/simulador.
    # Payload: list[str] -> Ej. ["P0300", "P0171"]
    datos_recibidos: Signal = Signal(list)

    # Señal Qt emitida ante cualquier excepción o fallo de conexión.
    # Payload: str -> Mensaje de error formateado para la GUI
    error_ocurrido: Signal = Signal(str)

    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        """
        Inicializa el trabajador asíncrono con una instancia del adaptador OBD.

        Args:
            adaptador (IAdaptadorOBD): Instancia de un adaptador que implementa
                                       la interfaz del contrato de hardware.
        """
        super().__init__()
        self.adaptador: IAdaptadorOBD = adaptador
        self._ejecutando: bool = True

    def run(self) -> None:
        """
        Punto de entrada del hilo (se ejecuta automáticamente al llamar a .start()).

        Intenta conectar al hardware, realiza la lectura de fallas DTC
        y notifica los resultados a la GUI mediante señales Qt.
        """
        try:
            # 1. Intentar establecer la conexión con el adaptador (físico o simulado)
            if self.adaptador.conectar():
                # 2. Leer la lista de códigos de falla activos
                dtcs: list[str] = self.adaptador.leer_dtcs()
                # 3. Notificar a la GUI transmitiendo la lista de códigos
                self.datos_recibidos.emit(dtcs)
            else:
                # 4. Manejar la falla de conexión si el adaptador retorna False
                self.error_ocurrido.emit(
                    "No se pudo establecer conexión con el adaptador OBD."
                )

        except Exception as e:
            # 5. Capturar excepciones de I/O o formato y notificar el error
            self.error_ocurrido.emit(f"Error durante la lectura OBD: {str(e)}")

    def detener(self) -> None:
        """
        Finaliza de manera limpia y segura la ejecución del hilo.

        Cambia la bandera de control, detiene el bucle de eventos
        y espera a que el hilo libere sus recursos.
        """
        self._ejecutando = False
        self.quit()  # Solicita al hilo finalizar su bucle de eventos
        self.wait()  # Bloquea hasta que la ejecución en segundo plano termine
