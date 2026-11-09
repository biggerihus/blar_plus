"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Centraliza el flujo de la aplicación ordenando las pantallas de Conductor y Mecánico,
administrando el estado de la conexión e integrando los módulos gráficos y ventanas emergentes.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación del módulo sys para gestión de argumentos de ejecución
import sys
# Importación de tipado estricto
from typing import List, Optional
# Importación de alineación y orientaciones de Qt
from PySide6.QtCore import Qt
# Importación de widgets principales de PySide6
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

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

        # Configuración de propiedades de la ventana
        self.setWindowTitle("Sistema de Monitoreo Vehicular - Blar Plus")
        self.resize(1100, 800)
        # Construcción e inicialización de componentes visuales
        self.iniciar_interfaz()

    # Método para inyectar la instancia de TrabajadorOBD
    def set_trabajador_obd(self, trabajador: TrabajadorOBD) -> None:
        """Inyecta la instancia de TrabajadorOBD y conecta sus señales Qt."""
        self.trabajador_obd = trabajador
        # Conexión de señal para actualizar banner con metadatos del vehículo
        self.trabajador_obd.info_vehiculo_recibida.connect(self.actualizar_info_vehiculo)
        # Conexión de señal para captura de errores y desconexiones físicas
        self.trabajador_obd.error_ocurrido.connect(self.recibir_error_asincrono)

    # Método para construir la estructura visual de la GUI
    def iniciar_interfaz(self) -> None:
        """Ensambla el diseño general integrando paneles, banners y botones."""
        # Widget central contenedor
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        # Layout vertical principal
        layout_principal = QVBoxLayout(widget_central)

        # Layout horizontal superior (Indicador y Botón de Conexión)
        layout_superior = QHBoxLayout()
        self.lbl_estado_texto = QLabel("Estado de Conexión: Desconectado")
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")

        btn_conectar = QPushButton("Conectar / Desconectar Equipo")
        btn_conectar.setStyleSheet(
            "color: black; font-weight: bold; background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px; border-radius: 4px;"
        )
        btn_conectar.clicked.connect(self.alternar_conexion)

        layout_superior.addWidget(self.lbl_estado_texto)
        layout_superior.addStretch()
        layout_superior.addWidget(btn_conectar)
        layout_principal.addLayout(layout_superior)

        # Banner dinámico de identificación del vehículo conectado
        self.lbl_banner_vehiculo = QLabel("🚘 Vehículo Monitoreado: NINGUNO (Equipo Desconectado)")
        self.lbl_banner_vehiculo.setStyleSheet(
            "background-color: #004D40; color: #E0F2F1; font-weight: bold; font-size: 13px; padding: 8px 12px; border-radius: 6px; border: 1px solid #00796B;"
        )
        layout_principal.addWidget(self.lbl_banner_vehiculo)

        # Selector de Vista (Conductor / Mecánico)
        layout_selector = QHBoxLayout()
        lbl_selector = QLabel("Selector de Vista:")
        lbl_selector.setStyleSheet("font-weight: bold; color: #FFFFFF;")

        self.combo_vista = QComboBox()
        self.combo_vista.addItems(["Vista Conductor", "Vista Mecánico"])
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

        # Barra de estado inferior con indicador LED
        self.barra_estado_widget = BarraEstadoWidget()
        layout_principal.addWidget(self.barra_estado_widget)

    # Método slot para actualizar el banner con información del vehículo
    def actualizar_info_vehiculo(self, info: dict) -> None:
        """Actualiza el texto del banner dinámico con vehículo, VIN y protocolo."""
        vehiculo = info.get("vehiculo", "Vehículo Estándar OBD-II")
        vin = info.get("vin", "N/D")
        protocolo = info.get("protocolo", "ISO 15765-4")
        self.lbl_banner_vehiculo.setText(
            f"🚘 Vehículo Monitoreado: {vehiculo}  |  VIN: {vin}  |  Protocolo: {protocolo}"
        )

    # Método slot para procesar y desplegar errores reportados por el hilo asíncrono
    def recibir_error_asincrono(self, mensaje_error: str) -> None:
        """
        Resetea la interfaz a estado neutro y despliega un mensaje modal limpio de error.
        """
        # Cambiar estado visual local a Desconectado
        self.estadoConexion = False
        self.lbl_estado_texto.setText("Estado de Conexión: Error / Desconectado")
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
        self.barra_estado_widget.actualizar_estado(False, f"Error: {mensaje_error}")
        self.lbl_resumen.setText("Resumen rápido: Fallo de comunicación con el vehículo.")
        self.lbl_banner_vehiculo.setText("🚘 Vehículo Monitoreado: NINGUNO (Error de Conexión)")

        # Restablecer marcadores numéricos a cero
        self.btn_vel.setText("Velocidad\n0.0 km/h")
        self.btn_temp.setText("Temperatura Motor\n0.0 °C")

        # Limpiar colecciones de reportes y redibujar interfaces vacías
        self.reportes_actuales = []
        self.lista_dtc_widget.cargar_reportes([])
        self.actualizar_vista_conductor_dtcs([])

        # Limpiar curvas del gráfico técnico
        if hasattr(self, "grafico_widget"):
            self.grafico_widget.limpiar_grafico()

        # Desplegar cuadro modal crítico utilizando formato de texto plano sin etiquetas HTML sueltas
        QMessageBox.critical(
            self,
            "Error de Comunicación OBD-II",
            f"No se pudo completar la operación o se perdió la conexión con el vehículo.\n\n"
            f"Detalle técnico del error:\n{mensaje_error}\n\n"
            f"Verifique que el escáner esté bien conectado al puerto del vehículo y el encendido activo."
        )

    # Método para construir la pantalla del conductor
    def crear_vista_conductor(self) -> QWidget:
        """Construye el panel de usuario orientado al conductor."""
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

    # Método para construir la pantalla avanzada del mecánico
    def crear_vista_mecanico(self) -> QWidget:
        """Construye el panel avanzado de diagnóstico para el mecánico."""
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
        """Genera tarjetas explicativas semaforizadas (🟢, 🟡, 🔴) según la gravedad."""
        while self.layout_fallas_conductor.count():
            item = self.layout_fallas_conductor.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
        """Alterna el estado de conexión e invoca la actualización de sondeos e interfaz."""
        if not self.estadoConexion:
            if self.trabajador_obd:
                exito_conexion = self.trabajador_obd.iniciar_sondeo()
                if not exito_conexion:
                    return

            self.estadoConexion = True
            self.lbl_estado_texto.setText("Estado de Conexión: Conectado")
            self.lbl_estado_texto.setStyleSheet("color: #5cb85c; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(True, "Conectado a la ECU correctamente.")
            self.lbl_resumen.setText("Resumen rápido: Sistema sincronizado y estable.")

        else:
            self.estadoConexion = False
            self.lbl_estado_texto.setText("Estado de Conexión: Desconectado")
            self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(False, "Desconectado del vehículo.")
            self.lbl_resumen.setText("Resumen rápido: Advertencia - Equipo desconectado.")

            if self.trabajador_obd:
                self.trabajador_obd.pausar_sondeo()

            self.lbl_banner_vehiculo.setText("🚘 Vehículo Monitoreado: NINGUNO (Equipo Desconectado)")

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

    # Slot para recibir la lista de códigos DTC crudos
    def recibir_dtcs_asincronos(self, dtcs_raw: List[str]) -> None:
        """Slot receptor para actualizar la lista de DTCs en la GUI."""
        if not self.estadoConexion:
            return

        codigos_actuales = [dto.codigo for dto in self.reportes_actuales]
        if codigos_actuales == dtcs_raw:
            return

        dtos: List[DTCDTO] = self.controlador_reporte.procesar_dtcs_raw(dtcs_raw)
        self.reportes_actuales = dtos
        self.lista_dtc_widget.cargar_reportes(self.reportes_actuales)
        self.actualizar_vista_conductor_dtcs(self.reportes_actuales)

    # Slot para recibir lecturas continuas de sensores
    def recibir_sensores_asincronos(self, datos_sensores: dict) -> None:
        """Slot receptor para actualizar marcadores y gráfica en vivo."""
        if not self.estadoConexion:
            return

        velocidad = datos_sensores.get("velocidad", 0.0)
        temperatura = datos_sensores.get("temperatura", 0.0)

        self.btn_vel.setText(f"Velocidad\n{velocidad:.1f} km/h")
        self.btn_temp.setText(f"Temperatura Motor\n{temperatura:.1f} °C")

        if hasattr(self.grafico_widget, "actualizar_grafico"):
            self.grafico_widget.actualizar_grafico(datos_sensores)

    # Slot para cambiar vista en QStackedWidget
    def cambiar_vista(self, index: int) -> None:
        """Cambia el panel visual activo."""
        self.stacked_vistas.setCurrentIndex(index)

    # Slot para solicitar el borrado de códigos DTC
    def abrir_dialogo_borrado(self) -> None:
        """Despliega cuadro de borrado previa verificación de conexión."""
        if not self.estadoConexion:
            QMessageBox.warning(
                self,
                "Sin Conexión Activa",
                "No hay ningún vehículo conectado. Por favor, conecte el equipo antes de intentar borrar los códigos DTC."
            )
            return

        codigos_seleccionados = self.lista_dtc_widget.obtener_codigos_seleccionados()

        dialogo = DialogoConfirmacion(self)
        resultado = dialogo.exec()

        if resultado == QDialog.DialogCode.Accepted:
            if self.trabajador_obd:
                self.trabajador_obd.solicitar_limpieza_dtc(
                    codigos_seleccionados if codigos_seleccionados else None
                )

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


# Punto de entrada directo de la GUI
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
