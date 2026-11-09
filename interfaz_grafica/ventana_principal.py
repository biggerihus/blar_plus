"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Centraliza el flujo de la aplicación ordenando las pantallas de Conductor y Mecánico,
administrando el estado de la conexión e integrando los módulos gráficos y ventanas emergentes.
Incluye estilos oscuros unificados y reactivos para todos los selectores desplegables.

Autor: Estrada Loaiza Rogelio y Erick Polanco Romero
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación del módulo sys para gestión de argumentos de ejecución
import sys
# Importación de tipado estricto
from typing import List, Optional
# Importación de alineación, temporizador y orientaciones de Qt
from PySide6.QtCore import Qt, QTimer
# Importación de widgets principales de PySide6 (incluyendo QListView para forzar delegado de QSS)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Importación de los adaptadores de hardware de la Capa 4 (HAL)
from abstraccion_de_hardware.adaptador_elm327 import AdaptadorELM327
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador

# Importación de la barra de estado con indicador LED
from interfaz_grafica.barra_estado import BarraEstadoWidget
# Importación del gráfico dinámico pyqtgraph
from interfaz_grafica.grafico_tiempo_real import GraficoTiempoRealWidget
# Importación del widget de tabla DTC
from interfaz_grafica.lista_dtc import ListaDTCWidget
# Importación del cuadro modal de confirmación
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
# Importación del controlador y DTO
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO
# Importación de la clase TrabajadorOBD para anotación de tipos
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD


# Clase VentanaPrincipal que hereda de QMainWindow
class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la interfaz de usuario Blar Plus.
    """

    # Constructor principal de la ventana
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        # Invocación del constructor base QMainWindow
        super().__init__(parent)
        # Bandera booleana del estado de conexión de la interfaz
        self.estadoConexion: bool = False
        # Instanciación del controlador de reportes
        self.controlador_reporte: ControladorReporte = ControladorReporte()
        # Almacenamiento local de reportes DTO activos
        self.reportes_actuales: List[DTCDTO] = []
        # Referencia al trabajador de comunicación asíncrona
        self.trabajador_obd: Optional[TrabajadorOBD] = None

        # Instancia persistente del simulador para mantener el estado de intentos y secuencia de fallas
        self._adaptador_simulador: Optional[AdaptadorSimulador] = None

        # Configuración de propiedades de la ventana principal
        self.setWindowTitle("Sistema de Monitoreo Vehicular - Blar Plus")
        self.resize(1100, 800)
        
        # Construcción e inicialización de componentes visuales
        self.iniciar_interfaz()

    # Método para inyectar la instancia de TrabajadorOBD
    def set_trabajador_obd(self, trabajador: TrabajadorOBD) -> None:
        """Inyecta la instancia de TrabajadorOBD y conecta sus señales Qt a la interfaz."""
        self.trabajador_obd = trabajador
        # Conexión de señal para actualizar banner con metadatos del vehículo
        self.trabajador_obd.info_vehiculo_recibida.connect(self.actualizar_info_vehiculo)
        # Conexión de señal para captura de errores y desconexiones físicas
        self.trabajador_obd.error_ocurrido.connect(self.recibir_error_asincrono)

    # Método para construir la estructura visual de la GUI
    def iniciar_interfaz(self) -> None:
        """Ensambla el diseño general integrando paneles, banners, selector de puerto y botones."""
        # Widget central contenedor
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        # Layout vertical principal
        layout_principal = QVBoxLayout(widget_central)

        # Cadena QSS estandarizada para dar diseño idéntico a todos los QComboBox del sistema
        self.estilo_selectores_unificado = """
            QComboBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
                min-width: 210px;
            }
            QComboBox:hover, QComboBox:focus {
                border: 2px solid #007ACC;
                background-color: #252525;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #007ACC;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 2px solid #007ACC;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 6px 10px;
                color: #FFFFFF;
                background-color: #1E1E1E;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {
                background-color: #007ACC;
                color: #FFFFFF;
                font-weight: bold;
            }
            QComboBox:disabled {
                background-color: #1A1A1A;
                color: #666666;
                border: 2px solid #333333;
            }
        """

        # ---------------- LAYOUT SUPERIOR (Controles de Conexión) ----------------
        layout_superior = QHBoxLayout()
        self.lbl_estado_texto = QLabel("Estado de Conexión: Desconectado")
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")

        # Selector de Puerto Serie / Modo de Operación
        lbl_puerto = QLabel("Puerto / Hardware:")
        lbl_puerto.setStyleSheet("color: #FFFFFF; font-weight: bold; margin-left: 10px;")

        self.combo_puerto_modo = QComboBox()
        self.combo_puerto_modo.setStyleSheet(self.estilo_selectores_unificado)
        # Forzar el delegado QListView para garantizar resaltado azul puro en hover
        self.combo_puerto_modo.setView(QListView())

        # Botón para escanear y refrescar puertos USB serie
        self.btn_refrescar_puertos = QPushButton("🔄 Escanear Puertos")
        self.btn_refrescar_puertos.setToolTip("Buscar y actualizar puertos USB serie conectados al equipo")
        self._restaurar_boton_refrescar()
        self.btn_refrescar_puertos.clicked.connect(self.refrescar_puertos_con_efecto)

        # Botón de Conexión/Desconexión
        btn_conectar = QPushButton("Conectar / Desconectar Equipo")
        btn_conectar.setStyleSheet(
            "color: black; font-weight: bold; background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px 12px; border-radius: 4px;"
        )
        btn_conectar.clicked.connect(self.alternar_conexion)

        # Agregar elementos al layout superior
        layout_superior.addWidget(self.lbl_estado_texto)
        layout_superior.addStretch()
        layout_superior.addWidget(lbl_puerto)
        layout_superior.addWidget(self.combo_puerto_modo)
        layout_superior.addWidget(self.btn_refrescar_puertos)
        layout_superior.addWidget(btn_conectar)
        layout_principal.addLayout(layout_superior)

        # Carga inicial de la lista de puertos en el menú desplegable
        self.actualizar_lista_puertos()

        # ---------------- BANNER DEL VEHÍCULO ----------------
        self.lbl_banner_vehiculo = QLabel("🚘 Vehículo Monitoreado: NINGUNO (Equipo Desconectado)")
        self.lbl_banner_vehiculo.setStyleSheet(
            "background-color: #004D40; color: #E0F2F1; font-weight: bold; font-size: 13px; padding: 8px 12px; border-radius: 6px; border: 1px solid #00796B;"
        )
        layout_principal.addWidget(self.lbl_banner_vehiculo)

        # ---------------- SELECTOR DE VISTAS (Conductor / Mecánico) ----------------
        layout_selector = QHBoxLayout()
        lbl_selector = QLabel("Selector de Vista:")
        lbl_selector.setStyleSheet("font-weight: bold; color: #FFFFFF;")

        self.combo_vista = QComboBox()
        self.combo_vista.addItems(["Vista Conductor", "Vista Mecánico"])
        self.combo_vista.setStyleSheet(self.estilo_selectores_unificado)
        # Forzar el delegado QListView para garantizar resaltado azul puro en hover
        self.combo_vista.setView(QListView())
        self.combo_vista.currentIndexChanged.connect(self.cambiar_vista)

        layout_selector.addWidget(lbl_selector)
        layout_selector.addWidget(self.combo_vista)
        layout_selector.addStretch()
        layout_principal.addLayout(layout_selector)

        # QStackedWidget contenedor de vistas intercambiables
        self.stacked_vistas = QStackedWidget()
        self.stacked_vistas.addWidget(self.crear_vista_conductor())
        self.stacked_vistas.addWidget(self.crear_vista_mecanico())
        layout_principal.addWidget(self.stacked_vistas)

        # ---------------- BARRA DE ESTADO INFERIOR ----------------
        self.barra_estado_widget = BarraEstadoWidget()
        layout_principal.addWidget(self.barra_estado_widget)

    # Método para refrescar la lista de puertos aplicando una animación brillante al botón
    def refrescar_puertos_con_efecto(self) -> None:
        """Refresca la lista de puertos aplicando una iluminación brillante temporal al botón."""
        if self.estadoConexion:
            return

        # Aplicar estilo brillante centelleante al botón durante la búsqueda
        self.btn_refrescar_puertos.setText("✨ Escaneando...")
        self.btn_refrescar_puertos.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: #FFFFFF;
                font-weight: bold;
                border: 2px solid #005999;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        QApplication.processEvents()

        # Actualizar la lista real de puertos
        self.actualizar_lista_puertos()

        # Emitir notificación visual en la barra de estado
        self.barra_estado_widget.actualizar_estado(
            self.estadoConexion, "Puertos serie rescanados con éxito."
        )

        # Restaurar el texto y estilo normal tras 800 ms
        QTimer.singleShot(800, self._restaurar_boton_refrescar)

    # Método auxiliar para restablecer el diseño normal del botón de escaneo
    def _restaurar_boton_refrescar(self) -> None:
        """Restablece la apariencia normal (gris) del botón de escaneo."""
        self.btn_refrescar_puertos.setText("🔄 Escanear Puertos")
        self.btn_refrescar_puertos.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #FFFFFF;
                font-weight: bold;
                border: 1px solid #555555;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:disabled {
                background-color: #222222;
                color: #666666;
                border: 1px solid #333333;
            }
        """)

    # Método para escanear y poblar los puertos serie disponibles
    def actualizar_lista_puertos(self) -> None:
        """Detecta los puertos serie disponibles en el sistema y actualiza el desplegable."""
        self.combo_puerto_modo.clear()
        # Escaneo de puertos serie mediante la Capa HAL
        puertos_detectados = AdaptadorELM327.detectar_puertos()

        # Inserción de cada puerto físico encontrado
        for puerto in puertos_detectados:
            self.combo_puerto_modo.addItem(f"🔌 ELM327 ({puerto})", puerto)

        # Inserción de la opción de simulador virtual (siempre al final)
        self.combo_puerto_modo.addItem("⚙️ Modo Simulador", "SIMULADOR")

        # Seleccionar por defecto el primer puerto real si existe, o el simulador en su defecto
        if puertos_detectados:
            self.combo_puerto_modo.setCurrentIndex(0)
        else:
            self.combo_puerto_modo.setCurrentIndex(self.combo_puerto_modo.count() - 1)

    # Método slot para actualizar el banner con información del vehículo
    def actualizar_info_vehiculo(self, info: dict) -> None:
        """Actualiza el texto del banner dinámico superior con marca, VIN y protocolo."""
        vehiculo = info.get("vehiculo", "Vehículo Estándar OBD-II")
        vin = info.get("vin", "N/D")
        protocolo = info.get("protocolo", "ISO 15765-4")
        self.lbl_banner_vehiculo.setText(
            f"🚘 Vehículo Monitoreado: {vehiculo}  |  VIN: {vin}  |  Protocolo: {protocolo}"
        )

    # Método slot para procesar y desplegar errores reportados por el hilo asíncrono
    def recibir_error_asincrono(self, mensaje_error: str) -> None:
        """
        Resetea la interfaz a estado neutro tras una desconexión y despliega un cuadro de error modal.
        """
        # Cambiar estado visual local a Desconectado
        self.estadoConexion = False
        self.lbl_estado_texto.setText("Estado de Conexión: Error / Desconectado")
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
        self.barra_estado_widget.actualizar_estado(False, f"Error: {mensaje_error}")
        self.lbl_resumen.setText("Resumen rápido: Fallo de comunicación con el vehículo.")
        self.lbl_banner_vehiculo.setText("🚘 Vehículo Monitoreado: NINGUNO (Error de Conexión)")

        # Re-habilitar los controles de selección de puerto y escaneo
        self.combo_puerto_modo.setEnabled(True)
        self.btn_refrescar_puertos.setEnabled(True)

        # Restablecer marcadores numéricos de la vista conductor a cero
        self.btn_vel.setText("Velocidad\n0.0 km/h")
        self.btn_temp.setText("Temperatura Motor\n0.0 °C")

        # Limpiar colecciones de reportes y redibujar interfaces vacías (DTCs)
        self.reportes_actuales = []
        self.lista_dtc_widget.cargar_reportes([])
        self.actualizar_vista_conductor_dtcs([])

        # Limpiar curvas del gráfico técnico del mecánico
        if hasattr(self, "grafico_widget"):
            self.grafico_widget.limpiar_grafico()

        # Desplegar cuadro modal crítico utilizando formato de texto plano
        QMessageBox.critical(
            self,
            "Error de Comunicación OBD-II",
            f"No se pudo completar la operación o se perdió la conexión con el vehículo.\n\n"
            f"Detalle técnico del error:\n{mensaje_error}\n\n"
            f"Verifique que el escáner esté bien conectado al puerto del vehículo y el encendido activo."
        )

    # Método para construir la pantalla del conductor (Vista Simple)
    def crear_vista_conductor(self) -> QWidget:
        """Construye el panel de usuario orientado al conductor (marcadores y tarjetas de salud)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel de Conductor - Indicadores y Salud Vehicular")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        layout_indicadores = QHBoxLayout()
        self.btn_vel = QPushButton("Velocidad\n0.0 km/h")
        self.btn_vel.setStyleSheet(
            "background-color: #1E1E1E; border: 2px solid #007ACC; border-radius: 12px; font-size: 18px; padding: 20px; font-weight: bold; color: #FFFFFF;"
        )

        self.btn_temp = QPushButton("Temperatura Motor\n0.0 °C")
        self.btn_temp.setStyleSheet(
            "background-color: #1E1E1E; border: 2px solid #28A745; border-radius: 12px; font-size: 18px; padding: 20px; font-weight: bold; color: #FFFFFF;"
        )

        layout_indicadores.addWidget(self.btn_vel)
        layout_indicadores.addWidget(self.btn_temp)
        layout.addLayout(layout_indicadores)

        self.lbl_resumen = QLabel("Resumen rápido: Sistema desconectado.")
        self.lbl_resumen.setStyleSheet(
            "font-size: 13px; background-color: #333333; padding: 10px; border-radius: 6px; border: 1px solid #555555; color: #FFFFFF;"
        )
        layout.addWidget(self.lbl_resumen)

        lbl_titulo_fallas = QLabel("Estado y Diagnóstico Comprensible para el Conductor:")
        lbl_titulo_fallas.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0; margin-top: 10px;")
        layout.addWidget(lbl_titulo_fallas)

        # Área con scroll para las tarjetas semaforizadas de DTC
        scroll_fallas = QScrollArea()
        scroll_fallas.setWidgetResizable(True)
        scroll_fallas.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        widget_fallas_interno = QWidget()
        self.layout_fallas_conductor = QVBoxLayout(widget_fallas_interno)
        self.layout_fallas_conductor.setContentsMargins(0, 0, 0, 0)
        self.layout_fallas_conductor.setSpacing(8)

        scroll_fallas.setWidget(widget_fallas_interno)
        layout.addWidget(scroll_fallas)

        self.actualizar_vista_conductor_dtcs([])
        return widget

    # Método para construir la pantalla avanzada del mecánico (Gráficas y Tabla DTC)
    def crear_vista_mecanico(self) -> QWidget:
        """Construye el panel avanzado de diagnóstico para el mecánico con splitter vertical."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel Técnico - Diagnóstico Avanzado y Sensores")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        splitter_mecanico = QSplitter(Qt.Orientation.Vertical)

        self.grafico_widget = GraficoTiempoRealWidget()
        splitter_mecanico.addWidget(self.grafico_widget)

        self.lista_dtc_widget = ListaDTCWidget()
        splitter_mecanico.addWidget(self.lista_dtc_widget)

        splitter_mecanico.setSizes([320, 380])
        layout.addWidget(splitter_mecanico)

        btn_borrar = QPushButton("Borrar Códigos de Diagnóstico (DTC)")
        btn_borrar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 10px; border-radius: 4px;"
        )
        btn_borrar.clicked.connect(self.abrir_dialogo_borrado)
        layout.addWidget(btn_borrar)

        return widget

    # Método para actualizar tarjetas semaforizadas del conductor
    def actualizar_vista_conductor_dtcs(self, dtos: List[DTCDTO]) -> None:
        """Genera tarjetas explicativas semaforizadas (🟢, 🟡, 🔴) según la gravedad de las fallas."""
        # Limpiar el layout actual
        while self.layout_fallas_conductor.count():
            item = self.layout_fallas_conductor.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Si no hay DTCs, mostrar tarjeta verde de estado excelente
        if not dtos:
            tarjeta_ok = QFrame()
            tarjeta_ok.setStyleSheet(
                "QFrame { background-color: #1B3820; border: 1px solid #28A745; border-radius: 6px; padding: 10px; }"
            )
            layout_ok = QHBoxLayout(tarjeta_ok)
            lbl_icono = QLabel("🟢")
            lbl_icono.setStyleSheet("font-size: 20px;")
            lbl_txt = QLabel("<b>Estado General: Excelente</b><br>No se detectan fallas mecánicas ni electrónicas registradas en la ECU.")
            lbl_txt.setStyleSheet("color: #FFFFFF; font-size: 13px;")
            layout_ok.addWidget(lbl_icono)
            layout_ok.addWidget(lbl_txt, stretch=1)
            self.layout_fallas_conductor.addWidget(tarjeta_ok)
            return

        # Generar tarjetas por cada DTC encontrado
        for dto in dtos:
            tarjeta = QFrame()
            gravedad = dto.gravedad.lower()

            if "alta" in gravedad:
                color_borde = "#E53935"
                color_fondo = "#3A1C1C"
                icono = "🔴"
                nivel = "CRÍTICO"
            elif "media" in gravedad:
                color_borde = "#FB8C00"
                color_fondo = "#3A2E1C"
                icono = "🟡"
                nivel = "ADVERTENCIA"
            else:
                color_borde = "#4CAF50"
                color_fondo = "#1C3A21"
                icono = "🟢"
                nivel = "INFORMATIVO"

            tarjeta.setStyleSheet(
                f"QFrame {{ background-color: {color_fondo}; border: 1px solid {color_borde}; border-radius: 6px; padding: 10px; }}"
            )
            layout_t = QHBoxLayout(tarjeta)

            lbl_ic = QLabel(icono)
            lbl_ic.setStyleSheet("font-size: 22px;")

            texto_explicativo = (
                f"<b style='color:{color_borde};'>[{nivel}] Falla en: {dto.categoria} ({dto.codigo})</b><br>"
                f"<span style='color: #FFFFFF;'><b>¿Qué significa?:</b> {dto.descripcion}</span><br>"
                f"<span style='color: #CCCCCC;'><b>Recomendación:</b> {dto.solucion}</span>"
            )
            lbl_desc = QLabel(texto_explicativo)
            lbl_desc.setWordWrap(True)

            layout_t.addWidget(lbl_ic)
            layout_t.addWidget(lbl_desc, stretch=1)
            self.layout_fallas_conductor.addWidget(tarjeta)

        self.layout_fallas_conductor.addStretch()

    # Método slot para alternar estado de conexión
    def alternar_conexion(self) -> None:
        """Alterna el estado de conexión e invoca el inicio/pausa del sondeo de hardware."""
        if not self.estadoConexion:
            # Obtención del identificador de puerto/hardware seleccionado
            valor_seleccionado = self.combo_puerto_modo.currentData()

            # Instanciación persistente para permitir que los intentos se acumulen correctamente
            if valor_seleccionado == "SIMULADOR":
                if self._adaptador_simulador is None:
                    self._adaptador_simulador = AdaptadorSimulador()
                nuevo_adaptador = self._adaptador_simulador
                puerto_target = None
            else:
                nuevo_adaptador = AdaptadorELM327()
                puerto_target = valor_seleccionado

            if self.trabajador_obd:
                # Reasignación del adaptador seleccionado al hilo de sondeo asíncrono
                self.trabajador_obd.adaptador = nuevo_adaptador
                exito_conexion = self.trabajador_obd.iniciar_sondeo(puerto=puerto_target)
                if not exito_conexion:
                    return

            self.estadoConexion = True
            self.lbl_estado_texto.setText("Estado de Conexión: Conectado")
            self.lbl_estado_texto.setStyleSheet("color: #5cb85c; font-weight: bold;")

            desc_conexion = f"Conectado ({valor_seleccionado})" if valor_seleccionado != "SIMULADOR" else "Conectado (Simulador)"
            self.barra_estado_widget.actualizar_estado(True, f"{desc_conexion} a la ECU correctamente.")
            self.lbl_resumen.setText("Resumen rápido: Sistema sincronizado y estable.")

            # Bloquear la modificación del selector de puertos y botón de escaneo durante la sesión activa
            self.combo_puerto_modo.setEnabled(False)
            self.btn_refrescar_puertos.setEnabled(False)

        else:
            # Rutina de Desconexión controlada
            self.estadoConexion = False
            self.lbl_estado_texto.setText("Estado de Conexión: Desconectado")
            self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(False, "Desconectado del vehículo.")
            self.lbl_resumen.setText("Resumen rápido: Advertencia - Equipo desconectado.")

            # Re-habilitar los controles de selección de puerto y escaneo
            self.combo_puerto_modo.setEnabled(True)
            self.btn_refrescar_puertos.setEnabled(True)

            if self.trabajador_obd:
                self.trabajador_obd.pausar_sondeo()

            self.lbl_banner_vehiculo.setText("🚘 Vehículo Monitoreado: NINGUNO (Equipo Desconectado)")

            # Resetear marcadores de la vista conductor
            self.btn_vel.setText("Velocidad\n0.0 km/h")
            self.btn_temp.setText("Temperatura Motor\n0.0 °C")

            self.reportes_actuales = []
            self.lista_dtc_widget.cargar_reportes([])
            self.actualizar_vista_conductor_dtcs([])

            if hasattr(self, "grafico_widget"):
                self.grafico_widget.limpiar_grafico()

            QMessageBox.information(
                self,
                "Conexión Finalizada",
                "El equipo ha sido desconectado correctamente del vehículo."
            )

    # Slot para recibir la lista de códigos DTC crudos desde el hilo secundario
    def recibir_dtcs_asincronos(self, dtcs_raw: List[str]) -> None:
        """Slot receptor para actualizar la lista de DTCs en la GUI."""
        if not self.estadoConexion:
            return

        # Evitar sobrecarga de UI si los códigos son los mismos
        codigos_actuales = [dto.codigo for dto in self.reportes_actuales]
        if codigos_actuales == dtcs_raw:
            return

        # Procesamiento de DTCs mediante el controlador y actualización de vistas
        dtos: List[DTCDTO] = self.controlador_reporte.procesar_dtcs_raw(dtcs_raw)
        self.reportes_actuales = dtos
        self.lista_dtc_widget.cargar_reportes(self.reportes_actuales)
        self.actualizar_vista_conductor_dtcs(self.reportes_actuales)

    # Slot para recibir lecturas continuas de sensores desde el hilo secundario
    def recibir_sensores_asincronos(self, datos_sensores: dict) -> None:
        """Slot receptor para actualizar marcadores y gráfica en vivo."""
        if not self.estadoConexion:
            return

        velocidad = datos_sensores.get("velocidad", 0.0)
        temperatura = datos_sensores.get("temperatura", 0.0)

        self.btn_vel.setText(f"Velocidad\n{velocidad:.1f} km/h")
        self.btn_temp.setText(f"Temperatura Motor\n{temperatura:.1f} °C")

        # Actualización de la gráfica pyqtgraph de la vista del mecánico
        if hasattr(self.grafico_widget, "actualizar_grafico"):
            self.grafico_widget.actualizar_grafico(datos_sensores)

    # Slot para cambiar vista en QStackedWidget
    def cambiar_vista(self, index: int) -> None:
        """Cambia el panel visual activo (Conductor o Mecánico)."""
        self.stacked_vistas.setCurrentIndex(index)

    # Slot para solicitar el borrado de códigos DTC a la ECU
    def abrir_dialogo_borrado(self) -> None:
        """Despliega cuadro de borrado de códigos DTC previa verificación de conexión."""
        if not self.estadoConexion:
            QMessageBox.warning(
                self,
                "Sin Conexión Activa",
                "No hay ningún vehículo conectado. Por favor, conecte el equipo antes de intentar borrar los códigos DTC."
            )
            return

        # Recuperar selección específica desde el componente de lista
        codigos_seleccionados = self.lista_dtc_widget.obtener_codigos_seleccionados()

        # Desplegar diálogo modal
        dialogo = DialogoConfirmacion(self)
        resultado = dialogo.exec()

        if resultado == QDialog.DialogCode.Accepted:
            if self.trabajador_obd:
                # Enviar solicitud asíncrona de borrado a través del controlador hardware
                self.trabajador_obd.solicitar_limpieza_dtc(
                    codigos_seleccionados if codigos_seleccionados else None
                )

            # Reflejo optimista de la eliminación en la memoria local
            if codigos_seleccionados:
                self.reportes_actuales = [
                    dto for dto in self.reportes_actuales if dto.codigo not in codigos_seleccionados
                ]
                mensaje = f"Se borraron {len(codigos_seleccionados)} código(s) seleccionado(s)."
            else:
                self.reportes_actuales = []
                mensaje = "Todos los códigos DTC fueron borrados de la memoria con éxito."

            self.barra_estado_widget.actualizar_estado(True, mensaje)
            self.lista_dtc_widget.cargar_reportes(self.reportes_actuales)
            self.actualizar_vista_conductor_dtcs(self.reportes_actuales)
        else:
            self.barra_estado_widget.actualizar_estado(True, "Operación de borrado cancelada por el usuario.")


# Punto de entrada directo de la GUI si se ejecuta este script por separado
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
