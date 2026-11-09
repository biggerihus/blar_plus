"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona continua entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread),
garantizando sondeos periódicos a 10 Hz sin bloquear la interfaz.

Autor: Erick Polanco Romero
"""

from PySide6.QtCore import QThread, Signal
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para el sondeo continuo de datos OBD-II.

    Realiza lecturas periódicas a 10 Hz (cada 100 ms) en segundo plano
    evitando el congelamiento de la GUI (Main Thread).

    Señales Qt (Atributos de Clase):
        datos_recibidos (Signal): Emite una lista de cadenas con los códigos DTC leídos.
        error_ocurrido (Signal): Emite una cadena con el mensaje descriptivo del fallo.
    """

    # Señal emitida al obtener exitosamente la lista de códigos DTC en cada ciclo.
    # Payload: list[str] -> Ej. ["P0300", "P0171"]
    datos_recibidos: Signal = Signal(list)

    # Señal emitida ante fallos de conexión o excepciones durante la lectura.
    # Payload: str -> Texto informativo del error para el usuario o log
    error_ocurrido: Signal = Signal(str)

    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        """
        Inicializa el trabajador asíncrono con una instancia del adaptador OBD.

        Args:
            adaptador (IAdaptadorOBD): Instancia del adaptador que implementa
                                       la interfaz de comunicación con el hardware.
        """
        super().__init__()
        self.adaptador: IAdaptadorOBD = adaptador
        self._ejecutando: bool = True  # Bandera de control para el bucle de sondeo continuo

    def run(self) -> None:
        """
        Punto de entrada del hilo secundario (se ejecuta al invocar .start()).

        Establece la conexión inicial con el hardware y mantiene un bucle de
        sondeo continuo a una frecuencia de 10 Hz (espera de 100 ms por iteración).
        """
        try:
            # 1. Intentar conexión inicial con el adaptador (físico o simulador)
            if not self.adaptador.conectar():
                self.error_ocurrido.emit(
                    "No se pudo establecer conexión con el adaptador OBD."
                )
                return

            # 2. Bucle de sondeo continuo mientras la bandera de control siga activa
            while self._ejecutando:
                try:
                    # Lectura síncrona de códigos DTC desde el bus/puerto
                    dtcs: list[str] = self.adaptador.leer_dtc()

                    # Transmitir los datos hacia la GUI mediante la señal Qt
                    self.datos_recibidos.emit(dtcs)
                except Exception as e:
                    # Notificar error en iteración de lectura sin tumbar abruptamente el hilo
                    self.error_ocurrido.emit(f"Error durante la lectura OBD: {str(e)}")

                # 3. Muestreo a 10 Hz: Pausa asíncrona de 100 ms en el hilo secundario
                self.msleep(100)

        except Exception as e:
            # Captura de fallos críticos no controlados en la infraestructura del hilo
            self.error_ocurrido.emit(f"Fallo crítico en el hilo de control: {str(e)}")

    def detener(self) -> None:
        """
        Finaliza de manera limpia y segura la ejecución del hilo secundario.

        Desactiva la bandera de control del bucle `while`, solicita la detención
        del event-loop de Qt y espera la liberación de recursos del hilo.
        """
        self._ejecutando = False
        self.quit()  # Detiene el bucle de eventos del hilo
        self.wait()  # Bloquea hasta que la ejecución en segundo plano termine completamente
