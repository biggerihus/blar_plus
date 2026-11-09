"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Centraliza el flujo de la aplicación ordenando las pantallas de Conductor y Mecánico,
administrando el estado de la conexión e integrando los módulos gráficos.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación de sys para manejo de argumentos de consola y salida del sistema
import sys
# Importación de List y Optional para anotaciones de tipo
from typing import List, Optional
# Importación de alineación y orientación de Qt
from PySide6.QtCore import Qt
# Importación de componentes principales de PySide6.QtWidgets para construir la GUI
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Importación del widget de barra de estado
from interfaz_grafica.barra_estado import BarraEstadoWidget
# Importación del widget de gráfico en tiempo real
from interfaz_grafica.grafico_tiempo_real import GraficoTiempoRealWidget
# Importación del widget de lista de códigos DTC
from interfaz_grafica.lista_dtc import ListaDTCWidget
# Importación del diálogo modal de confirmación
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
# Importación de la capa de control y su DTO
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO


# Clase VentanaPrincipal que hereda de QMainWindow para coordinar todo el sistema visual
class VentanaPrincipal(QMainWindow):
    """
    Ventana principal del sistema que coordina vistas, barras de estado y eventos.

    Atributos:
        estadoConexion (bool): Bandera del estado actual de enlace.
        controlador_reporte (ControladorReporte): Instancia de la Capa de Control.
        barra_estado_widget (BarraEstadoWidget): Widget del LED indicador.
        stacked_vistas (QStackedWidget): Contenedor multiventana.
        grafico_widget (GraficoTiempoRealWidget): Gráfico técnico de sensores.
        lista_dtc_widget (ListaDTCWidget): Tabla de diagnósticos DTC.
        layout_fallas_conductor (QVBoxLayout): Layout dinámico de tarjetas amigables para el conductor.
        reportes_actuales (List[DTCDTO]): Lista local de fallas activas procesadas.
    """

    # Constructor de la ventana principal que configura las vistas y controladores
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la ventana principal y sus propiedades base.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía.
        """
        # Invocación del constructor base de QMainWindow
        super().__init__(parent)
        # Bandera inicial de estado de conexión establecida en False
        self.estadoConexion: bool = False
        # Instanciación del controlador de reportes de la capa de control
        self.controlador_reporte: ControladorReporte = ControladorReporte()
        # Colección en memoria de reportes procesados
        self.reportes_actuales: List[DTCDTO] = []

        # Título de la ventana principal
        self.setWindowTitle("Sistema de Monitoreo Vehicular - Blar Plus")
        # Ajuste de tamaño inicial a 1100x800 píxeles
        self.resize(1100, 800)
        # Llamada al método de ensamblado de la interfaz gráfica
        self.iniciar_interfaz()

    # Método principal que crea la estructura visual de la ventana
    def iniciar_interfaz(self) -> None:
        """Ensambla el diseño general integrando los paneles y selectores."""
        # Widget central contenedor de la ventana principal
        widget_central = QWidget()
        # Asignación del widget central a la QMainWindow
        self.setCentralWidget(widget_central)
        # Layout vertical principal del widget central
        layout_principal = QVBoxLayout(widget_central)

        # Layout horizontal superior para el indicador de conexión y botón de enlace
        layout_superior = QHBoxLayout()
        # Etiqueta textual del estado de conexión
        self.lbl_estado_texto = QLabel("Estado de Conexión: Desconectado")
        # Aplicación de estilo rojo de advertencia
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")

        # Botón para cambiar el estado de conexión
        btn_conectar = QPushButton("Conectar / Desconectar Equipo")
        # Estilizado del botón de conexión con bordes y padding
        btn_conectar.setStyleSheet(
            "color: black; font-weight: bold; background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px; border-radius: 4px;"
        )
        # Conexión del evento clic del botón al método alternar_conexion
        btn_conectar.clicked.connect(self.alternar_conexion)

        # Inserción de la etiqueta en el layout superior
        layout_superior.addWidget(self.lbl_estado_texto)
        # Espaciador para empujar el botón a la derecha
        layout_superior.addStretch()
        # Inserción del botón en el layout superior
        layout_superior.addWidget(btn_conectar)
        # Adición del layout superior al layout principal
        layout_principal.addLayout(layout_superior)

        # Layout horizontal para el selector de vistas
        layout_selector = QHBoxLayout()
        # Etiqueta indicadora del selector en texto blanco de alto contraste
        lbl_selector = QLabel("Selector de Vista:")
        lbl_selector.setStyleSheet("font-weight: bold; color: #FFFFFF;")

        # Desplegable ComboBox para alternar entre Vista Conductor y Mecánico
        self.combo_vista = QComboBox()
        # Adición de las dos vistas disponibles
        self.combo_vista.addItems(["Vista Conductor", "Vista Mecánico"])
        # Conexión del evento de cambio de índice con el método cambiar_vista
        self.combo_vista.currentIndexChanged.connect(self.cambiar_vista)

        # Inserción de la etiqueta y combo en el layout del selector
        layout_selector.addWidget(lbl_selector)
        layout_selector.addWidget(self.combo_vista)
        layout_selector.addStretch()
        # Adición del layout de selector al layout principal
        layout_principal.addLayout(layout_selector)

        # Widget apilado QStackedWidget para gestionar el cambio dinámico de pantallas
        self.stacked_vistas = QStackedWidget()
        # Adición de la vista de conductor en la posición 0
        self.stacked_vistas.addWidget(self.crear_vista_conductor())
        # Adición de la vista de mecánico en la posición 1
        self.stacked_vistas.addWidget(self.crear_vista_mecanico())
        # Inserción del contenedor apilado en el layout principal
        layout_principal.addWidget(self.stacked_vistas)

        # Instanciación de la barra de estado con indicador LED
        self.barra_estado_widget = BarraEstadoWidget()
        # Inserción de la barra de estado al final del layout principal
        layout_principal.addWidget(self.barra_estado_widget)

    # Método para construir el panel responsivo del conductor
    def crear_vista_conductor(self) -> QWidget:
        """
        Construye y devuelve el panel visual diseñado para la vista del conductor.
        Incluye indicadores de alta visibilidad y tarjetas de fallas traducidas a lenguaje común.
        """
        # Widget contenedor de la vista
        widget = QWidget()
        # Layout vertical de la vista de conductor
        layout = QVBoxLayout(widget)

        # Título del panel de conductor
        lbl_titulo = QLabel("Panel de Conductor - Indicadores y Salud Vehicular")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        # Layout horizontal para los botones de indicadores principales
        layout_indicadores = QHBoxLayout()
        # Botón indicador de velocidad
        self.btn_vel = QPushButton("Velocidad\n0 km/h")
        self.btn_vel.setStyleSheet(
            "background-color: #1E1E1E; border: 2px solid #007ACC; border-radius: 12px; font-size: 18px; padding: 20px; font-weight: bold; color: #FFFFFF;"
        )

        # Botón indicador de temperatura del motor
        self.btn_temp = QPushButton("Temperatura Motor\n90 °C")
        self.btn_temp.setStyleSheet(
            "background-color: #1E1E1E; border: 2px solid #28A745; border-radius: 12px; font-size: 18px; padding: 20px; font-weight: bold; color: #FFFFFF;"
        )

        # Inserción de indicadores en el layout
        layout_indicadores.addWidget(self.btn_vel)
        layout_indicadores.addWidget(self.btn_temp)
        layout.addLayout(layout_indicadores)

        # Etiqueta de resumen rápido para el conductor
        self.lbl_resumen = QLabel("Resumen rápido: Sistema desconectado.")
        self.lbl_resumen.setStyleSheet(
            "font-size: 13px; background-color: #333333; padding: 10px; border-radius: 6px; border: 1px solid #555555; color: #FFFFFF;"
        )
        layout.addWidget(self.lbl_resumen)

        # Título de la sección de fallas amigables para el conductor
        lbl_titulo_fallas = QLabel("Estado y Diagnóstico Comprensible para el Conductor:")
        lbl_titulo_fallas.setStyleSheet("font-size: 14px; font-weight: bold; color: #E0E0E0; margin-top: 10px;")
        layout.addWidget(lbl_titulo_fallas)

        # Contenedor con ScrollArea para desplegar las tarjetas de diagnóstico sin saturar la pantalla
        scroll_fallas = QScrollArea()
        scroll_fallas.setWidgetResizable(True)
        scroll_fallas.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        widget_fallas_interno = QWidget()
        self.layout_fallas_conductor = QVBoxLayout(widget_fallas_interno)
        self.layout_fallas_conductor.setContentsMargins(0, 0, 0, 0)
        self.layout_fallas_conductor.setSpacing(8)

        scroll_fallas.setWidget(widget_fallas_interno)
        layout.addWidget(scroll_fallas)

        # Cargar estado inicial (Sin fallas)
        self.actualizar_vista_conductor_dtcs([])

        # Retorno del widget armado para la vista de conductor
        return widget

    # Método para construir el panel avanzado de diagnóstico del mecánico
    def crear_vista_mecanico(self) -> QWidget:
        """
        Construye e integra la vista técnica avanzada con gráficos y tabla de fallas.
        Utiliza un QSplitter vertical para permitir al mecánico redimensionar el espacio entre la gráfica y la tabla.
        """
        # Widget contenedor de la vista
        widget = QWidget()
        # Layout vertical para la vista de mecánico
        layout = QVBoxLayout(widget)

        # Título del panel mecánico
        lbl_titulo = QLabel("Panel Técnico - Diagnóstico Avanzado y Sensores")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF; margin-bottom: 5px;")
        layout.addWidget(lbl_titulo)

        # QSplitter vertical para permitir redimensionamiento dinámico entre la gráfica y la tabla
        splitter_mecanico = QSplitter(Qt.Orientation.Vertical)

        # Instanciación del widget de gráfico en tiempo real
        self.grafico_widget = GraficoTiempoRealWidget()
        splitter_mecanico.addWidget(self.grafico_widget)

        # Instanciación del widget de tabla de códigos DTC
        self.lista_dtc_widget = ListaDTCWidget()
        splitter_mecanico.addWidget(self.lista_dtc_widget)

        # Proporciones iniciales del QSplitter (40% gráfica, 60% tabla)
        splitter_mecanico.setSizes([320, 380])
        layout.addWidget(splitter_mecanico)

        # Botón para solicitar el borrado de códigos DTC
        btn_borrar = QPushButton("Borrar Códigos de Diagnóstico (DTC)")
        btn_borrar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 10px; border-radius: 4px;"
        )
        # Conexión del evento clic con el diálogo modal de borrado
        btn_borrar.clicked.connect(self.abrir_dialogo_borrado)
        layout.addWidget(btn_borrar)

        # Retorno del widget armado para la vista del mecánico
        return widget

    # Método para traducir DTOs técnicos a tarjetas semaforizadas y comprensibles para el conductor
    def actualizar_vista_conductor_dtcs(self, dtos: List[DTCDTO]) -> None:
        """
        Genera tarjetas de fallas comprensibles con semaforización (🟢, 🟡, 🔴) según la gravedad de los códigos DTC.

        Args:
            dtos (List[DTCDTO]): Lista de DTOs procesados por la capa de control.
        """
        # Limpieza de tarjetas anteriores en la interfaz del conductor
        while self.layout_fallas_conductor.count():
            item = self.layout_fallas_conductor.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Si el sistema no detecta fallas o está en buen estado
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

        # Generación de tarjetas para cada código presente
        for dto in dtos:
            tarjeta = QFrame()
            gravedad = dto.gravedad.lower()

            # Determinación de colores y semáforo según gravedad
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

    # Método slot para alternar el estado de la conexión
    def alternar_conexion(self) -> None:
        """Alterna el estado de la conexión e invoca las actualizaciones visuales."""
        # Inversión del valor booleano de conexión
        self.estadoConexion = not self.estadoConexion
        # Si se estableció conexión
        if self.estadoConexion:
            self.lbl_estado_texto.setText("Estado de Conexión: Conectado")
            self.lbl_estado_texto.setStyleSheet("color: #5cb85c; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(True, "Conectado a la ECU correctamente.")
            self.lbl_resumen.setText("Resumen rápido: Sistema sincronizado y estable.")
        # Si se cortó la conexión
        else:
            self.lbl_estado_texto.setText("Estado de Conexión: Desconectado")
            self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(False, "Desconectado del vehículo.")
            self.lbl_resumen.setText("Resumen rápido: Advertencia - Equipo desconectado.")

    # Slot para recibir la lista de códigos DTC crudos emitidos de forma asíncrona
    def recibir_dtcs_asincronos(self, dtcs_raw: List[str]) -> None:
        """
        Slot receptor para conectar las señales de TrabajadorOBD con la interfaz gráfica.
        Filtra actualizaciones innecesarias para no interferir con las casillas de la tabla.

        Args:
            dtcs_raw (List[str]): Lista de cadenas crudas DTC enviadas por el hilo secundario.
        """
        # Extraer los códigos actualmente cargados en memoria
        codigos_actuales = [dto.codigo for dto in self.reportes_actuales]

        # Si los códigos recibidos son idénticos a los que ya tenemos desplegados, omitimos la recarga
        if codigos_actuales == dtcs_raw:
            return

        # Procesamiento de tramas crudas a objetos DTO mediante la capa de control
        dtos: List[DTCDTO] = self.controlador_reporte.procesar_dtcs_raw(dtcs_raw)
        # Guardado en memoria local de los reportes recibidos
        self.reportes_actuales = dtos
        # Carga de la tabla visual con los DTOs formateados para el mecánico
        self.lista_dtc_widget.cargar_reportes(self.reportes_actuales)
        # Carga de tarjetas traducidas para la vista de conductor
        self.actualizar_vista_conductor_dtcs(self.reportes_actuales)

    # Método slot para cambiar la pantalla visible en el widget apilado
    def cambiar_vista(self, index: int) -> None:
        """Cambia el panel visible según el menú desplegable."""
        # Ajuste del índice activo en el QStackedWidget
        self.stacked_vistas.setCurrentIndex(index)

    # Método slot para desplegar el cuadro modal de borrado inteligente
    def abrir_dialogo_borrado(self) -> None:
        """
        Abre la ventana modal de seguridad para autorizar el borrado de códigos.
        Si hay casillas seleccionadas en la columna 'Sel.', borra sólo esas fallas; de lo contrario, borra todas.
        """
        # Obtener los códigos DTC marcados en las casillas de verificación de la tabla
        codigos_seleccionados = self.lista_dtc_widget.obtener_codigos_seleccionados()

        # Instanciación del diálogo modal de confirmación
        dialogo = DialogoConfirmacion(self)
        # Ejecución modal bloqueante y captura del resultado
        resultado = dialogo.exec()

        # Si el usuario presionó Confirmar
        if resultado == QDialog.DialogCode.Accepted:
            # Evaluar si el usuario seleccionó códigos específicos para borrar
            if codigos_seleccionados:
                # Filtrar la lista conservando sólo las fallas NO seleccionadas
                self.reportes_actuales = [
                    dto for dto in self.reportes_actuales if dto.codigo not in codigos_seleccionados
                ]
                # Mensaje de confirmación de borrado parcial
                mensaje = f"Se borraron {len(codigos_seleccionados)} código(s) seleccionado(s)."
            else:
                # Si no había casillas marcadas, vaciar la lista completa de fallas
                self.reportes_actuales = []
                # Mensaje de confirmación de borrado total
                mensaje = "Todos los códigos DTC fueron borrados de la memoria con éxito."

            # Actualizar la barra de estado con el resultado de la operación
            self.barra_estado_widget.actualizar_estado(True, mensaje)
            # Re-renderizar la tabla de mecánico con las fallas restantes
            self.lista_dtc_widget.cargar_reportes(self.reportes_actuales)
            # Re-renderizar las tarjetas del conductor con las fallas restantes
            self.actualizar_vista_conductor_dtcs(self.reportes_actuales)
        # Si el usuario canceló o cerró el diálogo
        else:
            self.barra_estado_widget.actualizar_estado(True, "Operación de borrado cancelada por el usuario.")


# Punto de entrada de ejecución directa de la interfaz gráfica
if __name__ == "__main__":
    # Inicialización de la aplicación de Qt
    app = QApplication(sys.argv)
    # Instanciación de la ventana principal
    ventana = VentanaPrincipal()
    # Renderizado en pantalla de la ventana
    ventana.show()
    # Ejecución del bucle principal de eventos Qt
    sys.exit(app.exec())
