"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Centraliza el flujo de la aplicación ordenando las pantallas de Conductor y Mecánico,
administrando el estado de la conexión e integrando los módulos gráficos.

Autor: Estrada Loaiza Rogelio
"""

import sys
from typing import List, Optional
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

from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.grafico_tiempo_real import GraficoTiempoRealWidget
from interfaz_grafica.lista_dtc import ListaDTCWidget
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la ventana principal y sus propiedades base.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía.
        """
        super().__init__(parent)
        self.estadoConexion: bool = False
        self.controlador_reporte: ControladorReporte = ControladorReporte()

        self.setWindowTitle("Sistema de Monitoreo Vehicular - Blar Plus")
        self.resize(1100, 800)
        self.iniciar_interfaz()

    def iniciar_interfaz(self) -> None:
        """Ensambla el diseño general integrando los paneles y selectores."""
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)

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

        layout_selector = QHBoxLayout()
        lbl_selector = QLabel("Selector de Vista:")
        lbl_selector.setStyleSheet("font-weight: bold;")

        self.combo_vista = QComboBox()
        self.combo_vista.addItems(["Vista Conductor", "Vista Mecánico"])
        self.combo_vista.currentIndexChanged.connect(self.cambiar_vista)

        layout_selector.addWidget(lbl_selector)
        layout_selector.addWidget(self.combo_vista)
        layout_selector.addStretch()
        layout_principal.addLayout(layout_selector)

        self.stacked_vistas = QStackedWidget()
        self.stacked_vistas.addWidget(self.crear_vista_conductor())
        self.stacked_vistas.addWidget(self.crear_vista_mecanico())
        layout_principal.addWidget(self.stacked_vistas)

        self.barra_estado_widget = BarraEstadoWidget()
        layout_principal.addWidget(self.barra_estado_widget)

    def crear_vista_conductor(self) -> QWidget:
        """Construye y devuelve el panel visual diseñado para la vista del conductor."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel de Conductor - Indicadores Generales")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        layout_indicadores = QHBoxLayout()
        self.btn_vel = QPushButton("Velocidad\n0 km/h")
        self.btn_vel.setStyleSheet(
            "background-color: #f7f7f7; border: 2px solid #ccc; border-radius: 12px; font-size: 18px; padding: 25px; font-weight: bold; color: black;"
        )

        self.btn_temp = QPushButton("Temperatura Motor\n90 °C")
        self.btn_temp.setStyleSheet(
            "background-color: #eaf2f8; border: 2px solid #a4bdfc; border-radius: 12px; font-size: 18px; padding: 25px; font-weight: bold; color: black;"
        )

        layout_indicadores.addWidget(self.btn_vel)
        layout_indicadores.addWidget(self.btn_temp)
        layout.addLayout(layout_indicadores)

        self.lbl_resumen = QLabel("Resumen rápido: Sistema desconectado.")
        self.lbl_resumen.setStyleSheet(
            "font-size: 13px; background-color: #fff3cd; padding: 10px; border-radius: 6px; border: 1px solid #ffeeba; color: black;"
        )
        layout.addWidget(self.lbl_resumen)
        layout.addStretch()

        return widget

    def crear_vista_mecanico(self) -> QWidget:
        """Construye e integra la vista técnica avanzada con gráficos y tabla de fallas."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel Técnico - Diagnóstico Avanzado y Sensores")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        self.grafico_widget = GraficoTiempoRealWidget()
        layout.addWidget(self.grafico_widget)

        self.lista_dtc_widget = ListaDTCWidget()
        layout.addWidget(self.lista_dtc_widget)

        btn_borrar = QPushButton("Borrar Códigos de Diagnóstico (DTC)")
        btn_borrar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 8px; border-radius: 4px;"
        )
        btn_borrar.clicked.connect(self.abrir_dialogo_borrado)
        layout.addWidget(btn_borrar)

        return widget

    def alternar_conexion(self) -> None:
        """Alterna el estado de la conexión e invoca las actualizaciones visuales."""
        self.estadoConexion = not self.estadoConexion
        if self.estadoConexion:
            self.lbl_estado_texto.setText("Estado de Conexión: Conectado")
            self.lbl_estado_texto.setStyleSheet("color: #5cb85c; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(True, "Conectado a la ECU correctamente.")
            self.lbl_resumen.setText("Resumen rápido: Sistema sincronizado y estable.")
        else:
            self.lbl_estado_texto.setText("Estado de Conexión: Desconectado")
            self.lbl_estado_texto.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.barra_estado_widget.actualizar_estado(False, "Desconectado del vehículo.")
            self.lbl_resumen.setText("Resumen rápido: Advertencia - Equipo desconectado.")

    def recibir_dtcs_asincronos(self, dtcs_raw: List[str]) -> None:
        """
        Slot receptor para conectar las señales de TrabajadorOBD con la interfaz gráfica.

        Args:
            dtcs_raw (List[str]): Lista de cadenas crudas DTC enviadas por el hilo secundario.
        """
        dtos: List[DTCDTO] = self.controlador_reporte.procesar_dtcs_raw(dtcs_raw)
        self.lista_dtc_widget.cargar_reportes(dtos)

    def cambiar_vista(self, index: int) -> None:
        """Cambia el panel visible según el menú desplegable."""
        self.stacked_vistas.setCurrentIndex(index)

    def abrir_dialogo_borrado(self) -> None:
        """Abre la ventana modal de seguridad para autorizar el borrado de la memoria."""
        dialogo = DialogoConfirmacion(self)
        resultado = dialogo.exec()

        if resultado == QDialog.DialogCode.Accepted:
            self.barra_estado_widget.actualizar_estado(True, "Códigos DTC borrados de la memoria con éxito.")
            self.lista_dtc_widget.cargar_reportes([])
        else:
            self.barra_estado_widget.actualizar_estado(True, "Operación de borrado cancelada.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
