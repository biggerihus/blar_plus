"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona continua entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread),
garantizando sondeos periódicos a 10 Hz y centralizando el cálculo de métricas de sesión.

Autor: Erick Polanco Romero
Capa: Núcleo y Controladores / Capa 2
"""

# Importación del módulo time para la medición real del tiempo de sesión
import time
# Importación de Optional para tipado de parámetros nulos
from typing import Optional

# Importación de QThread y Signal desde PySide6.QtCore
from PySide6.QtCore import QThread, Signal
# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase TrabajadorOBD que hereda de QThread para ejecutar sondeos asíncronos en segundo plano
class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para el sondeo continuo de datos OBD-II.

    Mide dinámicamente la duración de la sesión y enriquece las alertas
    de error cuando ocurre una desconexión en cualquier adaptador (Simulado o Real).
    """

    # Señal Qt para emitir la lista de códigos DTC leídos
    datos_recibidos: Signal = Signal(list)
    # Señal Qt para emitir el diccionario de telemetría de sensores en vivo
    sensores_recibidos: Signal = Signal(dict)
    # Señal Qt para emitir la información de identificación del vehículo
    info_vehiculo_recibida: Signal = Signal(dict)
    # Señal Qt para notificar errores de comunicación o desconexión
    error_ocurrido: Signal = Signal(str)

    # Constructor del trabajador asíncrono
    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        # Invocación del constructor base QThread
        super().__init__()
        # Asignación del adaptador de hardware inyectado
        self.adaptador: IAdaptadorOBD = adaptador
        # Bucle continuo de control del hilo
        self._ejecutando: bool = True
        # Bandera de activación del sondeo periódico de sensores
        self._sondeo_activo: bool = False

        # Timestamp exacto de inicio de la sesión de monitoreo (0.0 si está inactivo)
        self._tiempo_inicio_sesion: float = 0.0

    # Método privado para calcular y dar formato de texto plano a la duración de la sesión
    def _obtener_tiempo_sesion_formateado(self) -> str:
        """Calcula y formatea el tiempo transcurrido desde que se inició la sesión activa."""
        # Si la sesión no ha iniciado correctamente, retornar 0 s
        if self._tiempo_inicio_sesion <= 0:
            return "0 s"
        # Cálculo de los segundos totales transcurridos desde time.time()
        segundos_totales = int(time.time() - self._tiempo_inicio_sesion)
        # Extracción de minutos y segundos enteros
        minutos = segundos_totales // 60
        segundos = segundos_totales % 60
        # Retornar formato compuesto (ej. '1 min 20 s') o simple (ej. '40 s')
        return f"{minutos} min {segundos} s" if minutos > 0 else f"{segundos} s"

    # Método principal de entrada del hilo secundario ejecutado en segundo plano
    def run(self) -> None:
        """
        Bucle de ejecución continua a 10 Hz (cada 100 ms) mientras el sondeo esté activo.
        """
        while self._ejecutando:
            if self._sondeo_activo:
                try:
                    # Lectura síncrona de códigos DTC desde el adaptador
                    dtcs: list[str] = self.adaptador.leer_dtc()
                    # Emisión asíncrona de códigos hacia la GUI
                    self.datos_recibidos.emit(dtcs)

                    # Lectura síncrona del bloque de 10 sensores OBD-II
                    sensores: dict[str, float] = {
                        "rpm": self.adaptador.leer_pid("010C"),
                        "velocidad": self.adaptador.leer_pid("010D"),
                        "temperatura": self.adaptador.leer_pid("0105"),
                        "carga_motor": self.adaptador.leer_pid("0104"),
                        "posicion_acelerador": self.adaptador.leer_pid("0111"),
                        "maf": self.adaptador.leer_pid("0110"),
                        "sensor_o2": self.adaptador.leer_pid("0114"),
                        "iat": self.adaptador.leer_pid("010F"),
                        "nivel_combustible": self.adaptador.leer_pid("012F"),
                        "presion_map": self.adaptador.leer_pid("010B"),
                    }

                    # Emisión asíncrona del diccionario de telemetría hacia la GUI
                    self.sensores_recibidos.emit(sensores)

                except Exception as e:
                    # Pausar inmediatamente el sondeo ante cualquier excepción de comunicación
                    self._sondeo_activo = False
                    # Obtener la duración real calculada de la sesión
                    tiempo_fmt = self._obtener_tiempo_sesion_formateado()

                    # Emitir señal de error empaquetada con texto plano estandarizado con \n
                    self.error_ocurrido.emit(
                        f"Pérdida de comunicación tras {tiempo_fmt} de sesión activa.\nDetalle: {str(e)}"
                    )

            # Pausa asíncrona de 100 ms para mantener frecuencia de sondeo de 10 Hz
            self.msleep(100)

    # Método slot para iniciar la conexión y activar el sondeo
    def iniciar_sondeo(self) -> bool:
        """
        Intenta conectar con el adaptador de hardware y registra el inicio de la sesión.
        """
        try:
            # Verificar si el adaptador requiere inicialización de conexión
            if not getattr(self.adaptador, "conectado", False):
                if not self.adaptador.conectar():
                    # Emitir error si el intento de conexión física fue rechazado
                    self.error_ocurrido.emit(
                        "No se pudo detectar el adaptador OBD-II. Verifique que el cable esté conectado al puerto."
                    )
                    return False

            # Registrar el timestamp de inicio de la sesión activa
            self._tiempo_inicio_sesion = time.time()
            # Activar la bandera de sondeo continuo
            self._sondeo_activo = True

            # Consultar y emitir metadatos del vehículo conectado si el adaptador lo soporta
            if hasattr(self.adaptador, "obtener_info_vehiculo"):
                try:
                    info = self.adaptador.obtener_info_vehiculo()
                    self.info_vehiculo_recibida.emit(info)
                except Exception:
                    pass

            return True

        except Exception as e:
            # Emitir error en caso de fallo crítico al iniciar el canal
            self.error_ocurrido.emit(f"Fallo al conectar con el hardware: {str(e)}")
            return False

    # Método slot para pausar el sondeo y liberar recursos de hardware
    def pausar_sondeo(self) -> None:
        """Desactiva la bandera de sondeo y restablece el reloj de la sesión."""
        self._sondeo_activo = False
        self._tiempo_inicio_sesion = 0.0
        try:
            self.adaptador.desconectar()
        except Exception:
            pass

    # Método para solicitar el borrado de códigos DTC en segundo plano
    def solicitar_limpieza_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """Solicita la eliminación de DTCs al adaptador registrando posibles errores."""
        try:
            return self.adaptador.limpiar_dtc(codigos)
        except Exception as e:
            tiempo_fmt = self._obtener_tiempo_sesion_formateado()
            self.error_ocurrido.emit(
                f"Error al borrar códigos DTC tras {tiempo_fmt} de uso: {str(e)}"
            )
            return False

    # Método para detener limpia y de forma segura el hilo secundario QThread
    def detener(self) -> None:
        """Finaliza la ejecución del bucle secundario y espera su cierre completo."""
        self.pausar_sondeo()
        self._ejecutando = False
        self.quit()
        self.wait()
