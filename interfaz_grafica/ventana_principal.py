"""
Módulo de la Ventana Principal del Sistema Blar Plus.

Coordina la interfaz gráfica central integrando los módulos de barra de estado,
alternancia de vistas dinámicas (Conductor/Mecánico) y la visualización de datos.

Autor: Estrada Loaiza Rogelio
"""

import sys
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.lista_dtc import ListaDTCWidget


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación que administra los flujos de pantalla.

    Utiliza un `QStackedWidget` para alternar entre el Panel de Conductor
    y el Panel Técnico de Mecánico.

    Atributos:
        estadoConexion (bool): Almacena la condición actual de la conexión OBD.
        barra_estado (BarraEstadoWidget): Widget reutilizable del LED de estado.
        stacked_vistas (QStackedWidget): Contenedor multiventana de la GUI.
        widget_dtc (ListaDTCWidget): Tabla de diagnósticos dentro de la vista técnico.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Inicializa las configuraciones globales de la ventana principal."""
        super().__init__(parent)
        self.estadoConexion: bool = False

        self.setWindowTitle("Ventana Principal - Sistema de Monitoreo Vehicular")
        self.resize(950, 600)
        self.iniciar()

    def iniciar(self) -> None:
        """Construye y ensambla todos los módulos visuales de la ventana principal."""
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)

        # --- Seccion 1: Barra Superior con BarraEstadoWidget ---
        layout_superior = QHBoxLayout()
        self.barra_estado = BarraEstadoWidget()

        btn_conectar = QPushButton("Conectar Equipo")
        btn_conectar.setStyleSheet(
            "color: black; font-weight: bold; background-color: #f0f0f0; border: 1px solid #ccc; padding: 6px; border-radius: 4px;"
        )
        btn_conectar.clicked.connect(self.conectarEquipo)

        layout_superior.addWidget(self.barra_estado)
        layout_superior.addWidget(btn_conectar)
        layout_principal.addLayout(layout_superior)

        # --- Seccion 2: Selector Responsivo de Vista ---
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

        # --- Seccion 3: QStackedWidget (Pila de Pantallas) ---
        self.stacked_vistas = QStackedWidget()
        self.stacked_vistas.addWidget(self.crear_vista_conductor())  # Índice 0
        self.stacked_vistas.addWidget(self.crear_vista_mecanico())   # Índice 1

        layout_principal.addWidget(self.stacked_vistas)

        # Sincronización inicial del resumen rápido
        self.mostrarResultado()

    def conectarEquipo(self) -> None:
        """Invierte el estado de la conexión e invoca la actualización del widget de estado."""
        self.estadoConexion = not self.estadoConexion
        if self.estadoConexion:
            self.barra_estado.actualizar_estado(True, "Conectado")
        else:
            self.barra_estado.actualizar_estado(False, "Desconectado")
        self.mostrarResultado()

    def mostrarResultado(self) -> None:
        """Actualiza el texto descriptivo en el resumen dinámico."""
        if self.estadoConexion:
            self.lbl_resumen.setText(
                "Resumen rápido: Sistema sincronizado. Todos los parámetros son estables."
            )
        else:
            self.lbl_resumen.setText(
                "Resumen rápido: Advertencia - Equipo desconectado. No se reciben datos."
            )

    def cambiar_vista(self, index: int) -> None:
        """Modifica el índice visible dentro del QStackedWidget."""
        self.stacked_vistas.setCurrentIndex(index)

    def crear_vista_conductor(self) -> QWidget:
        """Construye y retorna el panel adaptado para la vista rápida de un conductor."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel de Conductor - Indicadores Generales")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        # Contenedores de velocímetro y temperatura
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

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet(
            "font-size: 13px; background-color: #fff3cd; padding: 10px; border-radius: 6px; border: 1px solid #ffeeba; color: black;"
        )
        layout.addWidget(self.lbl_resumen)
        layout.addStretch()

        return widget

    def crear_vista_mecanico(self) -> QWidget:
        """Construye e integra la vista avanzada integrando el componente `ListaDTCWidget`."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        lbl_titulo = QLabel("Panel Técnico - Diagnóstico Avanzado")
        lbl_titulo.setStyleSheet("font-size: 15px; font-weight: bold; color: #333;")
        layout.addWidget(lbl_titulo)

        # Integración limpia del widget de tabla DTC refactorizado
        self.widget_dtc = ListaDTCWidget()
        layout.addWidget(self.widget_dtc)

        return widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())
