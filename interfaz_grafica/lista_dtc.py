"""
Módulo de Presentación de Diagnósticos DTC para Blar Plus.

Construye una tabla dinámica interactiva encargada de presentar los códigos de falla (DTC),
clasificándolos visualmente con patrones de color condicional en función de su severidad.

Autor: Estrada Loaiza Rogelio
"""

from typing import List, Optional, Union
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from nucleo_y_controladores.controlador_reporte import DTCDTO


class DTCReporte:
    """
    Estructura de datos para compatibilidad directa con reportes DTC.

    Atributos:
        codigo (str): Identificador estándar del fallo (ej. 'P0300').
        categoria (str): Área del vehículo afectada (ej. 'Encendido').
        gravedad (str): Evaluación de impacto ('Alta', 'Media', 'Baja').
        descripcion (str): Resumen técnico de la falla.
        solucion (str): Acción de mantenimiento sugerida.
    """

    def __init__(
        self,
        codigo: str,
        categoria: str,
        gravedad: str,
        descripcion: str,
        solucion: str,
    ) -> None:
        self.codigo = codigo
        self.categoria = categoria
        self.gravedad = gravedad
        self.descripcion = descripcion
        self.solucion = solucion


class ListaDTCWidget(QWidget):
    """
    Widget de tabla responsiva para la inspección detallada de códigos DTC.

    Atributos:
        tabla (QTableWidget): Componente que despliega la información organizada en 5 columnas.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa el widget y llama a la configuración de la tabla.

        Args:
            parent (Optional[QWidget]): Widget contenedor padre.
        """
        super().__init__(parent)
        self.inicializar_interfaz()

    def inicializar_interfaz(self) -> None:
        """Configura la estructura de columnas y las reglas de estiramiento del contenedor."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Construcción de la tabla con 5 columnas técnicas
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Código",
            "Categoría",
            "Gravedad",
            "Descripción",
            "Solución",
        ])

        # Estiramiento uniforme de las columnas a lo largo del espacio visible
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout_principal.addWidget(self.tabla)

    def cargar_reportes(self, reportes: List[Union[DTCReporte, DTCDTO]]) -> None:
        """
        Limpia la tabla y carga la lista de reportes aplicando formato de color según la gravedad.

        - Alta: Fondo rojo claro (#f8d7da), texto rojo oscuro (#721c24).
        - Media: Fondo amarillo claro (#fff3cd), texto marrón (#856404).
        - Baja: Fondo verde claro (#d4edda), texto verde oscuro (#155724).

        Args:
            reportes (List[Union[DTCReporte, DTCDTO]]): Colección de fallas a renderizar.
        """
        self.tabla.setRowCount(0)  # Limpieza de registros previos
        self.tabla.setRowCount(len(reportes))  # Dimensionamiento exacto de filas

        for row_idx, reporte in enumerate(reportes):
            item_codigo = QTableWidgetItem(reporte.codigo)
            item_categoria = QTableWidgetItem(reporte.categoria)
            item_gravedad = QTableWidgetItem(reporte.gravedad)
            item_descripcion = QTableWidgetItem(reporte.descripcion)
            item_solucion = QTableWidgetItem(reporte.solucion)

            item_gravedad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Asignación cromática basada en el texto de gravedad
            gravedad_lower = reporte.gravedad.strip().lower()
            if gravedad_lower == "alta":
                item_gravedad.setBackground(QColor("#f8d7da"))
                item_gravedad.setForeground(QColor("#721c24"))
            elif gravedad_lower == "media":
                item_gravedad.setBackground(QColor("#fff3cd"))
                item_gravedad.setForeground(QColor("#856404"))
            elif gravedad_lower == "baja":
                item_gravedad.setBackground(QColor("#d4edda"))
                item_gravedad.setForeground(QColor("#155724"))

            # Inserción de las celdas en la fila activa
            self.tabla.setItem(row_idx, 0, item_codigo)
            self.tabla.setItem(row_idx, 1, item_categoria)
            self.tabla.setItem(row_idx, 2, item_gravedad)
            self.tabla.setItem(row_idx, 3, item_descripcion)
            self.tabla.setItem(row_idx, 4, item_solucion)
