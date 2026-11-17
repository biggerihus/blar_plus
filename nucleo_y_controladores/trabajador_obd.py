"""
Módulo de Control de Concurrencia para Blar Plus.

Gestiona la comunicación asíncrona continua entre la capa de Hardware (HAL)
y la Capa de Interfaz Gráfica (GUI) mediante hilos secundarios (QThread),
garantizando sondeos seguros sin saturar el bus CAN del vehículo y serializando
las operaciones críticas (como el borrado Servicio 04) para evitar colisiones
en el puerto físico USB/UART.

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
# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


# Clase TrabajadorOBD que hereda de QThread para ejecutar sondeos asíncronos en segundo plano
class TrabajadorOBD(QThread):
    """
    Hilo de ejecución secundario para el sondeo continuo de datos OBD-II.

    Mide dinámicamente la duración de la sesión, protege el ancho de banda del bus CAN,
    serializa las órdenes de borrado de DTC dentro del propio hilo de hardware y
    notifica errores reales de comunicación o desconexión.

    Señales Qt:
        datos_recibidos (list): Emite la lista de códigos DTC activos leídos de la ECU.
        sensores_recibidos (dict): Emite el diccionario con lecturas de telemetría en vivo.
        info_vehiculo_recibida (dict): Emite los metadatos de identificación del vehículo.
        error_ocurrido (str): Emite mensajes descriptivos ante fallos físicos o de enlace.
        borrado_completado (bool, list): Emite el resultado del Servicio 04 (éxito/rechazo)
            junto con la lista de códigos solicitados para borrar.
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

    # Constructor del trabajador asíncrono
    def __init__(self, adaptador: IAdaptadorOBD) -> None:
        """
        Inicializa el hilo trabajador, las banderas de control y el cerrojo de concurrencia.

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

        # Cerrojo de exclusión mutua para encolar órdenes de borrado desde el hilo GUI
        self._lock_borrado: threading.Lock = threading.Lock()
        # Bandera que indica si existe una petición de Servicio 04 pendiente de ejecutarse
        self._borrado_pendiente: bool = False
        # Lista opcional de códigos específicos solicitados para depuración
        self._codigos_a_borrar: Optional[list[str]] = None

    def _obtener_tiempo_sesion_formateado(self) -> str:
        """
        Calcula y formatea el tiempo transcurrido desde que se inició la sesión activa.

        Returns:
            str: Duración formateada en minutos y segundos (ej. '1 min 15 s' o '24 s').
        """
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

        Args:
            pid (str): Código hexadecimal del parámetro OBD-II (ej. '010C').

        Returns:
            float: Valor numérico decodificado del sensor o 0.0 ante trama aislada corrupta.
        """
        try:
            valor = self.adaptador.leer_pid(pid)
            return float(valor) if valor is not None else 0.0
        except ValueError:
            # Trama aislada corrupta en bus serial: conservar lectura neutra sin desconectar
            return 0.0

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
            # Ejecución exclusiva en hardware sin concurrencia con lecturas de PIDs
            exito_borrado: bool = bool(self.adaptador.limpiar_dtc(codigos_objetivo))
            # Forzar re-lectura inmediata de DTCs (Modo 03) en este mismo ciclo
            self._contador_ciclos = 0
            # Notificar resultado real de la ECU de vuelta al hilo principal (GUI)
            self.borrado_completado.emit(exito_borrado, codigos_objetivo or [])

    def run(self) -> None:
        """
        Bucle de ejecución continua mientras el sondeo esté activo.
        Procesa primero órdenes críticas encoladas (borrado) y luego consulta DTCs y PIDs.
        """
        while self._ejecutando:
            if self._sondeo_activo:
                try:
                    # 1. Atender cualquier orden de borrado encolada antes de consultar sensores
                    self._procesar_borrado_pendiente()

                    # 2. Consultar códigos DTC (Modo 03) en el primer ciclo y luego cada 15 ciclos (~1.5s)
                    if self._contador_ciclos % 15 == 0:
                        dtcs: list[str] = self.adaptador.leer_dtc()
                        self.datos_recibidos.emit(dtcs)

                    self._contador_ciclos += 1

                    # 3. Lectura síncrona del bloque de sensores OBD-II (Modo 01)
                    sensores: dict[str, float] = {
                        "rpm": self._leer_pid_seguro("010C"),
                        "velocidad": self._leer_pid_seguro("010D"),
                        "temperatura": self._leer_pid_seguro("0105"),
                        "carga_motor": self._leer_pid_seguro("0104"),
                        "posicion_acelerador": self._leer_pid_seguro("0111"),
                        "maf": self._leer_pid_seguro("0110"),
                        "sensor_o2": self._leer_pid_seguro("0114"),
                        "iat": self._leer_pid_seguro("010F"),
                        "nivel_combustible": self._leer_pid_seguro("012F"),
                        "presion_map": self._leer_pid_seguro("010B"),
                    }

                    # Emisión asíncrona del diccionario de telemetría hacia la GUI
                    self.sensores_recibidos.emit(sensores)

                except Exception as e:
                    # Pausar inmediatamente el sondeo ante cualquier excepción física de hardware
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
        Intenta conectar con el adaptador de hardware y registra el inicio de la sesión.

        Args:
            puerto (Optional[str]): Ruta del puerto serie USB o None para simulador.

        Returns:
            bool: True si el enlace con el adaptador se estableció correctamente.
        """
        try:
            if hasattr(self.adaptador, "conectar"):
                resultado = (
                    self.adaptador.conectar(puerto=puerto)
                    if puerto
                    else self.adaptador.conectar()
                )
                if resultado is False:
                    self.error_ocurrido.emit(
                        "No se pudo detectar el adaptador OBD-II. Verifique el puerto y las conexiones físicas."
                    )
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
            self.error_ocurrido.emit(f"Fallo al conectar con el hardware: {str(e)}")
            return False

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

        Args:
            codigos (Optional[list[str]]): Lista de códigos específicos o None para borrado global.

        Returns:
            bool: True si la orden fue encolada (o ejecutada si el hilo no estaba activo).
        """
        # Si el hilo secundario está corriendo, encolar para ejecución exclusiva en run()
        if self.isRunning() and self._sondeo_activo:
            with self._lock_borrado:
                self._codigos_a_borrar = list(codigos) if codigos is not None else None
                self._borrado_pendiente = True
            return True

        # Respaldo síncrono en caso de invocación directa sin hilo activo (pruebas unitarias)
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
        """Finaliza la ejecución del bucle secundario y espera su cierre completo."""
        self.pausar_sondeo()
        self._ejecutando = False
        self.quit()
        self.wait()
