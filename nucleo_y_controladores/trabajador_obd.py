"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona continua entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread),
garantizando sondeos periódicos a 10 Hz sin bloquear la interfaz.

Autor: Erick Polanco Romero
Capa: Núcleo y Controladores / Capa 2
"""

# Importacion de QThread para ejecucion asincrona en segundo plano y Signal para comunicacion Qt
from PySide6.QtCore import QThread, Signal
# Importacion de la interfaz abstracta del adaptador hardware
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase TrabajadorOBD que hereda de QThread para ejecutar sondeos asincronos sin congelar la GUI
class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para el sondeo continuo de datos OBD-II.

    Realiza lecturas periódicas a 10 Hz (cada 100 ms) en segundo plano
    evitando el congelamiento de la GUI (Main Thread).

    Señales Qt (Atributos de Clase):
        datos_recibidos (Signal): Emite una lista de cadenas con los códigos DTC leídos.
        error_ocurrido (Signal): Emite una cadena con el mensaje descriptivo del fallo.
    """

    # Definicion de la señal Qt que transmite la lista de codigos DTC hacia la interfaz
    datos_recibidos: Signal = Signal(list)

    # Definicion de la señal Qt que notifica incidencias o errores de comunicacion
    error_ocurrido: Signal = Signal(str)

    # Constructor del hilo trabajador que recibe la instancia del adaptador de hardware
    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        """
        Inicializa el trabajador asíncrono con una instancia del adaptador OBD.

        Args:
            adaptador (IAdaptadorOBD): Instancia del adaptador que implementa
                                       la interfaz de comunicación con el hardware.
        """
        # Invocacion del constructor base de QThread
        super().__init__()
        # Asignacion del adaptador de hardware recibido
        self.adaptador: IAdaptadorOBD = adaptador
        # Inicializacion de la bandera de ejecucion del bucle continuo
        self._ejecutando: bool = True

    # Metodo principal de entrada del hilo asincrono ejecutado en segundo plano
    def run(self) -> None:
        """
        Punto de entrada del hilo secundario (se ejecuta al invocar .start()).

        Establece la conexión inicial con el hardware y mantiene un bucle de
        sondeo continuo a una frecuencia de 10 Hz (espera de 100 ms por iteración).
        """
        # Bloque try general para la captura de excepciones durante el ciclo de vida del hilo
        try:
            # Intento de establecimiento de conexion con el dispositivo OBD
            if not self.adaptador.conectar():
                # Emision de señal de error si falla la conexion inicial
                self.error_ocurrido.emit(
                    "No se pudo establecer conexión con el adaptador OBD."
                )
                # Finalizacion temprana de la ejecucion del metodo run
                return

            # Bucle de sondeo continuo en segundo plano mientras la bandera continue activa
            while self._ejecutando:
                # Bloque try interno para tolerar fallas de lectura sin romper el bucle principal
                try:
                    # Lectura sincrona de codigos DTC desde el adaptador
                    dtcs: list[str] = self.adaptador.leer_dtc()

                    # Transmision asincrona de los codigos DTC a la GUI mediante la señal Qt
                    self.datos_recibidos.emit(dtcs)
                # Captura de excepciones producidas durante una iteracion de lectura
                except Exception as e:
                    # Notificacion del error especifico a la GUI mediante la señal Qt
                    self.error_ocurrido.emit(f"Error durante la lectura OBD: {str(e)}")

                # Pausa asincrona de 100 milisegundos en el hilo secundario para lograr sondeo a 10 Hz
                self.msleep(100)

        # Captura de fallos criticos a nivel de infraestructura del hilo
        except Exception as e:
            # Emision del mensaje de falla critica final
            self.error_ocurrido.emit(f"Fallo crítico en el hilo de control: {str(e)}")

    # Metodo para detener de forma segura el hilo asincrono
    def detener(self) -> None:
        """
        Finaliza de manera limpia y segura la ejecución del hilo secundario.

        Desactiva la bandera de control del bucle `while`, solicita la detención
        del event-loop de Qt y espera la liberación de recursos del hilo.
        """
        # Desactivacion de la bandera de control del bucle while
        self._ejecutando = False
        # Solicitud de detencion del bucle de eventos interno de QThread
        self.quit()
        # Bloqueo síncrono hasta que el hilo en segundo plano haya terminado completamente
        self.wait()
