"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona continua entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread),
ejecutando tanto la negociación inicial (handshake) como los sondeos y borrados
(Servicio 04) fuera del hilo principal para evitar bloqueos en Wayland/Linux.

Autor: Erick Polanco Romero
Capa: Núcleo y Controladores / Capa 2
"""

# Importación de threading para sincronización segura entre el hilo GUI y el hilo OBD
import threading
# Importación del módulo time para la medición real del tiempo de sesión
import time
# Importación de Optional para tipado de parámetros nulos
from typing import Optional

# Importación de QThread y Signal desde PySide6.QtCore
from PySide6.QtCore import QThread, Signal
# Importación de QApplication para mantener activo el bucle de eventos durante la conexión
from PySide6.QtWidgets import QApplication
# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase TrabajadorOBD que hereda de QThread para ejecutar sondeos asíncronos en segundo plano
class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para la conexión y el sondeo continuo de datos OBD-II.

    Ejecuta la apertura y negociación del puerto serial en segundo plano sin congelar
    el hilo gráfico (evitando alertas de 'No responde' en Wayland), protege el ancho
    de banda del bus CAN y serializa las órdenes de borrado de DTC (Servicio 04).
    """

    # Señal Qt para emitir la lista de códigos DTC leídos
    datos_recibidos: Signal = Signal(list)
    # Señal Qt para emitir el diccionario de telemetría de sensores en vivo
    sensores_recibidos: Signal = Signal(dict)
    # Señal Qt para emitir la información de identificación del vehículo
    info_vehiculo_recibida: Signal = Signal(dict)
    # Señal Qt para notificar errores de comunicación o desconexión
    error_ocurrido: Signal = Signal(str)
    # Señal Qt para notificar a la GUI cuando el hilo secundario termina el borrado en la ECU
    borrado_completado: Signal = Signal(bool, list)

    # Lista ordenada de los 10 sensores consultados en cada ciclo
    PIDS_TELEMETRIA: tuple[tuple[str, str], ...] = (
        ("rpm", "010C"),
        ("velocidad", "010D"),
        ("temperatura", "0105"),
        ("carga_motor", "0104"),
        ("posicion_acelerador", "0111"),
        ("maf", "0110"),
        ("sensor_o2", "0114"),
        ("iat", "010F"),
        ("nivel_combustible", "012F"),
        ("presion_map", "010B"),
    )

    # Constructor del trabajador asíncrono
    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        """
        Inicializa el hilo trabajador, las banderas de control y los cerrojos de concurrencia.

        Args:
            adaptador (IAdaptadorOBD): Instancia concreta del adaptador de hardware o simulador.
        """
        super().__init__()
        # Referencia al adaptador de hardware activo (ELM327 o Simulador)
        self.adaptador: IAdaptadorOBD = adaptador
        # Bandera maestra de ciclo de vida del hilo QThread
        self._ejecutando: bool = True
        # Bandera que habilita o pausa las consultas al bus OBD-II
        self._sondeo_activo: bool = False
        # Marca de tiempo Unix en segundos del inicio de la sesión actual
        self._tiempo_inicio_sesion: float = 0.0
        # Contador de ciclos para espaciar lecturas lentas (DTCs) en bus CAN real
        self._contador_ciclos: int = 0

        # Sincronización para ejecutar el handshake de conexión en el hilo secundario
        self._lock_conexion: threading.Lock = threading.Lock()
        self._conexion_pendiente: bool = False
        self._puerto_pendiente: Optional[str] = None
        self._evento_conexion: threading.Event = threading.Event()
        self._resultado_conexion: bool = False

        # Cerrojo de exclusión mutua para encolar órdenes de borrado desde el hilo GUI
        self._lock_borrado: threading.Lock = threading.Lock()
        # Bandera que indica si existe una petición de Servicio 04 pendiente de ejecutarse
        self._borrado_pendiente: bool = False
        # Lista opcional de códigos específicos solicitados para depuración
        self._codigos_a_borrar: Optional[list[str]] = None

    def _obtener_tiempo_sesion_formateado(self) -> str:
        """Calcula y formatea el tiempo transcurrido desde que se inició la sesión activa."""
        if self._tiempo_inicio_sesion <= 0:
            return "0 s"
        segundos_totales = int(time.time() - self._tiempo_inicio_sesion)
        minutos = segundos_totales // 60
        segundos = segundos_totales % 60
        return f"{minutos} min {segundos} s" if minutos > 0 else f"{segundos} s"

    def _leer_pid_seguro(self, pid: str) -> float:
        """
        Lee un PID del adaptador. Tolera errores puntuales de formato de trama (ValueError)
        sin cerrar la sesión, pero propaga errores físicos de hardware (RuntimeError).
        """
        try:
            valor = self.adaptador.leer_pid(pid)
            return float(valor) if valor is not None else 0.0
        except ValueError:
            # Trama aislada corrupta en bus serial: conservar lectura neutra sin desconectar
            return 0.0

    def _ejecutar_conexion_interna(self, puerto: Optional[str] = None) -> bool:
        """Realiza la apertura del puerto y negociación de protocolo con el adaptador."""
        try:
            if hasattr(self.adaptador, "conectar"):
                resultado = (
                    self.adaptador.conectar(puerto=puerto)
                    if puerto
                    else self.adaptador.conectar()
                )
                if not self._ejecutando:
                    return False
                if resultado is False:
                    self.error_ocurrido.emit(
                        "No se pudo detectar el adaptador OBD-II. Verifique el puerto y las conexiones físicas."
                    )
                    return False

            if not self._ejecutando:
                return False

            with self._lock_borrado:
                self._borrado_pendiente = False
                self._codigos_a_borrar = None

            self._tiempo_inicio_sesion = time.time()
            self._contador_ciclos = 0
            self._sondeo_activo = True

            if hasattr(self.adaptador, "obtener_info_vehiculo"):
                try:
                    info = self.adaptador.obtener_info_vehiculo()
                    self.info_vehiculo_recibida.emit(info)
                except Exception:
                    pass
            else:
                self.info_vehiculo_recibida.emit({
                    "vehiculo": "Vehículo Simulado (Modo Pruebas)",
                    "vin": "SIM-BLAR-2026-OK",
                    "protocolo": "CAN 11bit / 500kbps (Simulado)",
                })

            return True

        except Exception as e:
            if self._ejecutando:
                self.error_ocurrido.emit(f"Fallo al conectar con el hardware: {str(e)}")
            return False

    def _procesar_conexion_pendiente(self) -> None:
        """Ejecuta en el hilo secundario una solicitud de conexión encolada desde la GUI."""
        with self._lock_conexion:
            if not self._conexion_pendiente:
                return
            puerto_obj = self._puerto_pendiente
            self._conexion_pendiente = False

        try:
            self._resultado_conexion = self._ejecutar_conexion_interna(puerto_obj)
        finally:
            self._evento_conexion.set()

    def _procesar_borrado_pendiente(self) -> None:
        """
        Verifica de forma thread-safe si existe una orden de borrado (Servicio 04)
        encolada por la interfaz y la ejecuta de forma exclusiva en el puerto serial.
        """
        ejecutar_borrado: bool = False
        codigos_objetivo: Optional[list[str]] = None

        with self._lock_borrado:
            if self._borrado_pendiente:
                ejecutar_borrado = True
                codigos_objetivo = (
                    list(self._codigos_a_borrar)
                    if self._codigos_a_borrar is not None
                    else None
                )
                self._borrado_pendiente = False
                self._codigos_a_borrar = None

        if ejecutar_borrado:
            exito_borrado: bool = bool(self.adaptador.limpiar_dtc(codigos_objetivo))
            self._contador_ciclos = 0
            self.borrado_completado.emit(exito_borrado, codigos_objetivo or [])

    def run(self) -> None:
        """
        Bucle de ejecución continua en segundo plano.
        Atiende primero conexiones pendientes, luego borrados (Servicio 04) y
        finalmente el sondeo continuo de DTCs y sensores OBD-II.
        """
        while self._ejecutando:
            if self._conexion_pendiente:
                self._procesar_conexion_pendiente()
                continue

            if self._sondeo_activo:
                try:
                    # 1. Atender cualquier orden de borrado encolada antes de consultar sensores
                    self._procesar_borrado_pendiente()

                    if not self._ejecutando or not self._sondeo_activo:
                        continue

                    # 2. Consultar códigos DTC (Modo 03) en el primer ciclo y luego cada 15 ciclos
                    if self._contador_ciclos % 15 == 0:
                        dtcs: list[str] = self.adaptador.leer_dtc()
                        if self._ejecutando and self._sondeo_activo:
                            self.datos_recibidos.emit(dtcs)

                    self._contador_ciclos += 1

                    # 3. Lectura del bloque de sensores OBD-II (Modo 01) con salida anticipada
                    sensores: dict[str, float] = {}
                    for clave, pid in self.PIDS_TELEMETRIA:
                        if not self._ejecutando or not self._sondeo_activo:
                            break
                        sensores[clave] = self._leer_pid_seguro(pid)

                    # Emisión asíncrona solo si el ciclo completó con la sesión aún activa
                    if self._ejecutando and self._sondeo_activo and len(sensores) == len(self.PIDS_TELEMETRIA):
                        self.sensores_recibidos.emit(sensores)

                except Exception as e:
                    # Si la sesión fue detenida manualmente por el usuario, no reportar como falla
                    if not self._ejecutando or not self._sondeo_activo:
                        continue
                    self._sondeo_activo = False
                    tiempo_fmt = self._obtener_tiempo_sesion_formateado()
                    self.error_ocurrido.emit(
                        f"Pérdida de comunicación tras {tiempo_fmt} de sesión activa.\nDetalle: {str(e)}"
                    )

            # En hardware real USB dar 150 ms de respiro al UART; en simulador mantener 100 ms (10 Hz)
            es_hardware_real = getattr(self.adaptador, "_serial", None) is not None
            self.msleep(150 if es_hardware_real else 100)

    def iniciar_sondeo(self, puerto: Optional[str] = None) -> bool:
        """
        Delega la negociación del hardware al hilo secundario mientras mantiene activo
        el bucle de eventos de Qt para evitar bloqueos de ventana en Wayland/Linux.
        """
        if not self.isRunning():
            self.start()

        if self.isRunning() and QThread.currentThread() != self:
            with self._lock_conexion:
                self._puerto_pendiente = puerto
                self._resultado_conexion = False
                self._evento_conexion.clear()
                self._conexion_pendiente = True

            app = QApplication.instance()
            while not self._evento_conexion.is_set() and self._ejecutando:
                if app is not None:
                    app.processEvents()
                self.msleep(20)

            if app is not None:
                app.processEvents()

            return self._resultado_conexion

        return self._ejecutar_conexion_interna(puerto)

    def pausar_sondeo(self) -> None:
        """Desactiva la bandera de sondeo, limpia órdenes pendientes y restablece el reloj."""
        self._sondeo_activo = False
        self._tiempo_inicio_sesion = 0.0
        with self._lock_borrado:
            self._borrado_pendiente = False
            self._codigos_a_borrar = None
        try:
            self.adaptador.desconectar()
        except Exception:
            pass

    def solicitar_limpieza_dtc(self, codigos: Optional[list[str]] = None) -> bool:
        """
        Encola de forma thread-safe una solicitud de borrado (Servicio 04) para que
        el propio hilo secundario la ejecute sin colisionar con el puerto serial.
        """
        if self.isRunning() and self._sondeo_activo:
            with self._lock_borrado:
                self._codigos_a_borrar = list(codigos) if codigos is not None else None
                self._borrado_pendiente = True
            return True

        try:
            exito: bool = bool(self.adaptador.limpiar_dtc(codigos))
            self._contador_ciclos = 0
            self.borrado_completado.emit(exito, list(codigos) if codigos else [])
            return exito
        except Exception as e:
            tiempo_fmt = self._obtener_tiempo_sesion_formateado()
            self.error_ocurrido.emit(
                f"Error al borrar códigos DTC tras {tiempo_fmt} de uso: {str(e)}"
            )
            return False

    def detener(self) -> None:
        """Finaliza la ejecución del bucle secundario y espera su cierre completo sin abortar."""
        self._ejecutando = False
        self._evento_conexion.set()
        self.pausar_sondeo()
        if self.isRunning():
            self.quit()
            if not self.wait(5000):
                self.terminate()
                self.wait(1000)
