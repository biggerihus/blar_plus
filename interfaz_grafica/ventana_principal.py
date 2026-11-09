"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Centraliza el flujo de la aplicación ordenando las pantallas de Conductor y Mecánico,
administrando el estado de la conexión e integrando los módulos gráficos.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importacion de sys para manejo de argumentos de consola y salida del sistema
import sys
# Importacion de List y Optional para anotaciones de tipo
from typing import List, Optional
# Importacion de componentes principales de PySide6.QtWidgets para construir la GUI
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Importacion del widget de barra de estado
from interfaz_grafica.barra_estado import BarraEstadoWidget
# Importacion del widget de grafico en tiempo real
from interfaz_grafica.grafico_tiempo_real import GraficoTiempoRealWidget
# Importacion del widget de lista de codigos DTC
from interfaz_grafica.lista_dtc import ListaDTCWidget
# Importacion del dialogo modal de confirmacion
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
# Importacion de la capa de control y su DTO
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
    """

    # Constructor de la ventana principal que configura las vistas y controladores
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la ventana principal y sus propiedades base.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía.
        """
        # Invocacion del constructor base de QMainWindow
        super().__init__(parent)
        # Bandera inicial de estado de conexion establecida en False
        self.estadoConexion: bool = False
        # Instanciacion del controlador de reportes de la capa de control
        self.controlador_reporte: ControladorReporte = ControladorReporte()

        # Titulo de la ventana principal
        self.setWindowTitle("Sistema de Monitoreo Vehicular - Blar Plus")
        # Ajuste de tamaño inicial a 1100x800 pixeles
        self.resize(1100, 800)
        # Llamada al metodo de ensamblado de la interfaz grafica
        self.iniciar_interfaz()

    # Metodo principal que crea la estructura visual de la ventana
    def iniciar_interfaz(self) -> None:
        """Ensambla el diseño general integrando los paneles y selectores."""
        # Widget central contenedor de la ventana principal
        widget_central = QWidget()
        # Asignacion del widget central a la QMainWindow
        self.setCentralWidget(widget_central)
        # Layout vertical principal del widget central
        layout_principal = QVBoxLayout(widget_central)

        # Layout horizontal superior para el indicador de conexion y boton de enlace
        layout_superior = QHBoxLayout()
        # Etiqueta textual del estado de conexion
        self.lbl_estado_texto = QLabel("Estado de Conexión: Desconectado")
        # Aplicacion de estilo rojo de advertencia
        self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")

        # Boton para cambiar el estado de conexion
        btn_conectar = QPushButton("Conectar / Desconectar Equipo")
        # Estilizado del boton de conexion con bordes y padding
        btn_conectar.setStyleSheet(
            "color: black; font-weight: bold; background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px; border-radius: 4px;"
        )
        # Conexion del evento clic del boton al metodo alternar_conexion
        btn_conectar.clicked.connect(self.alternar_conexion)

        # Insercion de la etiqueta en el layout superior
        layout_superior.addWidget(self.lbl_estado_texto)
        # Espaciador para empujar el boton a la derecha
        layout_superior.addStretch()
        # Insercion del boton en el layout superior
        layout_superior.addWidget(btn_conectar)
        # Adicion del layout superior al layout principal
        layout_principal.addLayout(layout_superior)

        # Layout horizontal para el selector de vistas
        layout_selector = QHBoxLayout()
        # Etiqueta indicadora del selector
        lbl_selector = QLabel("Selector de Vista:")
        lbl_selector.setStyleSheet("font-weight: bold;")

        # Desplegable ComboBox para alternar entre Vista Conductor y Mecanico
        self.combo_vista = QComboBox()
        # Adicion de las dos vistas disponibles
        self.combo_vista.addItems(["Vista Conductor", "Vista Mecánico"])
        # Conexion del evento de cambio de indice con el metodo cambiar_vista
        self.combo_vista.currentIndexChanged.connect(self.cambiar_vista)

        # Insercion de la etiqueta y combo en el layout del selector
        layout_selector.addWidget(lbl_selector)
        layout_selector.addWidget(self.combo_vista)
        layout_selector.addStretch()
        # Adicion del layout de selector al layout principal
        layout_principal.addLayout(layout_selector)

        # Widget apilado QStackedWidget para gestionar el cambio dinamico de pantallas
        self.stacked_vistas = QStackedWidget()
        # Adicion de la vista de conductor en la posicion 0
        self.stacked_vistas.addWidget(self.crear_vista_conductor())
        # Adicion de la vista de mecanico en la posicion 1
        self.stacked_vistas.addWidget(self.crear_vista_mecanico())
        # Insercion del contenedor apilado en el layout principal
        layout_principal.addWidget(self.stacked_vistas)

        # Instanciacion de la barra de estado con indicador LED
        self.barra_estado_widget = BarraEstadoWidget()
        # Insercion de la barra de estado al final del layout principal
        layout_principal.addWidget(self.barra_estado_widget)

    # Metodo para construir el panel responsivo del conductor
    def crear_vista_conductor(self) -> QWidget:
        """Construye y devuelve el panel visual diseñado para la vista del conductor."""
        # Widget contenedor de la vista
        widget = QWidget()
        # Layout vertical de la vista de conductor
        layout = QVBoxLayout(widget)

        # Titulo del panel de conductor
        lbl_titulo = QLabel("Panel de Conductor - Indicadores Generales")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        # Layout horizontal para los botones de indicadores principales
        layout_indicadores = QHBoxLayout()
        # Boton indicador de velocidad
        self.btn_vel = QPushButton("Velocidad\n0 km/h")
        self.btn_vel.setStyleSheet(
            "background-color: #f7f7f7; border: 2px solid #ccc; border-radius: 12px; font-size: 18px; padding: 25px; font-weight: bold; color: black;"
        )

        # Boton indicador de temperatura del motor
        self.btn_temp = QPushButton("Temperatura Motor\n90 °C")
        self.btn_temp.setStyleSheet(
            "background-color: #eaf2f8; border: 2px solid #a4bdfc; border-radius: 12px; font-size: 18px; padding: 25px; font-weight: bold; color: black;"
        )

        # Insercion de indicadores en el layout
        layout_indicadores.addWidget(self.btn_vel)
        layout_indicadores.addWidget(self.btn_temp)
        layout.addLayout(layout_indicadores)

        # Etiqueta de resumen rapido para el conductor
        self.lbl_resumen = QLabel("Resumen rápido: Sistema desconectado.")
        self.lbl_resumen.setStyleSheet(
            "font-size: 13px; background-color: #fff3cd; padding: 10px; border-radius: 6px; border: 1px solid #ffeeba; color: black;"
        )
        layout.addWidget(self.lbl_resumen)
        layout.addStretch()

        # Retorno del widget armado para la vista de conductor
        return widget

    # Metodo para construir el panel avanzado de diagnostico del mecanico
    def crear_vista_mecanico(self) -> QWidget:
        """Construye e integra la vista técnica avanzada con gráficos y tabla de fallas."""
        # Widget contenedor de la vista
        widget = QWidget()
        # Layout vertical para la vista de mecanico
        layout = QVBoxLayout(widget)

        # Titulo del panel mecanico
        lbl_titulo = QLabel("Panel Técnico - Diagnóstico Avanzado y Sensores")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        # Instanciacion del widget de grafico en tiempo real
        self.grafico_widget = GraficoTiempoRealWidget()
        layout.addWidget(self.grafico_widget)

        # Instanciacion del widget de tabla de codigos DTC
        self.lista_dtc_widget = ListaDTCWidget()
        layout.addWidget(self.lista_dtc_widget)

        # Boton para solicitar el borrado de codigos DTC
        btn_borrar = QPushButton("Borrar Códigos de Diagnóstico (DTC)")
        btn_borrar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 8px; border-radius: 4px;"
        )
        # Conexion del evento clic con el dialogo modal de borrado
        btn_borrar.clicked.connect(self.abrir_dialogo_borrado)
        layout.addWidget(btn_borrar)

        # Retorno del widget armado para la vista del mecanico
        return widget

    # Metodo slot para alternar el estado de la conexion
    def alternar_conexion(self) -> None:
        """Alterna el estado de la conexión e invoca las actualizaciones visuales."""
        # Inversion del valor booleano de conexion
        self.estadoConexion = not self.estadoConexion
        # Si se establecio conexion
        if self.estadoConexion:
            self.lbl_estado_texto.setText("Estado de Conexión: Conectado")
            self.lbl_estado_texto.setStyleSheet("color: #5cb85c; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(True, "Conectado a la ECU correctamente.")
            self.lbl_resumen.setText("Resumen rápido: Sistema sincronizado y estable.")
        # Si se corto la conexion
        else:
            self.lbl_estado_texto.setText("Estado de Conexión: Desconectado")
            self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(False, "Desconectado del vehículo.")
            self.lbl_resumen.setText("Resumen rápido: Advertencia - Equipo desconectado.")

    # Slot para recibir la lista de codigos DTC crudos emitidos de forma asincrona
    def recibir_dtcs_asincronos(self, dtcs_raw: List[str]) -> None:
        """
        Slot receptor para conectar las señales de TrabajadorOBD con la interfaz gráfica.

        Args:
            dtcs_raw (List[str]): Lista de cadenas crudas DTC enviadas por el hilo secundario.
        """
        # Procesamiento de tramas crudas a objetos DTO mediante la capa de control
        dtos: List[DTCDTO] = self.controlador_reporte.procesar_dtcs_raw(dtcs_raw)
        # Carga de la tabla visual con los DTOs formateados
        self.lista_dtc_widget.cargar_reportes(dtos)

    # Metodo slot para cambiar la pantalla visible en el widget apilado
    def cambiar_vista(self, index: int) -> None:
        """Cambia el panel visible según el menú desplegable."""
        # Ajuste del indice activo en el QStackedWidget
        self.stacked_vistas.setCurrentIndex(index)

    # Metodo slot para desplegar el cuadro modal de borrado
    def abrir_dialogo_borrado(self) -> None:
        """Abre la ventana modal de seguridad para autorizar el borrado de la memoria."""
        # Instanciacion del dialogo modal de confirmacion
        dialogo = DialogoConfirmacion(self)
        # Ejecucion modal bloqueante y captura del resultado
        resultado = dialogo.exec()

        # Si el usuario presiono Confirmar
        if resultado == QDialog.DialogCode.Accepted:
            self.barra_estado_widget.actualizar_estado(True, "Códigos DTC borrados de la memoria con éxito.")
            self.lista_dtc_widget.cargar_reportes([])
        # Si el usuario cancelo o cerro el dialogo
        else:
            self.barra_estado_widget.actualizar_estado(True, "Operación de borrado cancelada.")


# Punto de entrada de ejecucion directa de la interfaz grafica
if __name__ == "__main__":
    # Inicializacion de la aplicacion de Qt
    app = QApplication(sys.argv)
    # Instanciacion de la ventana principal
    ventana = VentanaPrincipal()
    # Renderizado en pantalla de la ventana
    ventana.show()
    # Ejecucion del bucle principal de eventos Qt
    sys.exit(app.exec())
