"""
Módulo de Presentación de Diagnósticos DTC para Blar Plus.

Define las estructuras de datos y el widget de tabla encargados de
desplegar de forma interactiva y legible los códigos de falla (DTC)
obtenidos desde la Capa de Control.

Autor: Estrada Loaiza Rogelio
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class DTCReporte:
    """
    Contenedor de información simplificado para representar un código de falla DTC.

    Atributos:
        codigo (str): Código estándar OBD-II (ej. 'P0300').
        categoria (str): Sistema del vehículo afectado (ej. 'Encendido', 'Admisión').
        gravedad (str): Severidad del fallo ('Alta', 'Media', 'Baja').
        descripcion (str): Detalle técnico del fallo detectado.
        solucion (str): Procedimiento correctivo sugerido.
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
    Widget de interfaz gráfica especializado en maquetar y ordenar fallas DTC.

    Implementa una tabla adaptativa con renderizado condicional de colores
    en función del nivel de severidad registrado.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Constructor del widget de la lista DTC.

        Args:
            parent (Optional[QWidget]): Widget contenedor padre en la jerarquía de Qt.
        """
        super().__init__(parent)
        self.inicializar_interfaz()

    def inicializar_interfaz(self) -> None:
        """Configura la tabla principal, sus encabezados y comportamientos de estiramiento."""
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # 1. Instanciación de la tabla de datos
        self.tabla_dtc = QTableWidget()
        self.tabla_dtc.setColumnCount(5)
        self.tabla_dtc.setHorizontalHeaderLabels([
            "Código",
            "Categoría",
            "Gravedad",
            "Descripción",
            "Solución",
        ])

        # 2. Configuración de responsividad: Las columnas ocupan proporcionalmente todo el espacio disponible
        self.tabla_dtc.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout_principal.addWidget(self.tabla_dtc)

    def cargar_reportes(self, reportes: List[DTCReporte]) -> None:
        """
        Limpia las filas existentes e inserta la nueva colección de reportes DTC.

        Aplica formato de color a las celdas según el nivel de severidad:
        - Alta: Fondo rojo claro (#f8d7da), texto oscuro (#721c24).
        - Media: Fondo amarillo claro (#fff3cd), texto oscuro (#856404).
        - Baja: Fondo verde claro (#d4edda), texto oscuro (#155724).

        Args:
            reportes (List[DTCReporte]): Lista de instancias de `DTCReporte` a desplegar.
        """
        # 1. Limpieza y preparación del tamaño de la tabla
        self.tabla_dtc.setRowCount(0)
        self.tabla_dtc.setRowCount(len(reportes))

        # 2. Iteración y carga de celdas
        for row_idx, reporte in enumerate(reportes):
            item_codigo = QTableWidgetItem(reporte.codigo)
            item_categoria = QTableWidgetItem(reporte.categoria)
            item_gravedad = QTableWidgetItem(reporte.gravedad)
            item_descripcion = QTableWidgetItem(reporte.descripcion)
            item_solucion = QTableWidgetItem(reporte.solucion)

            # Alineación centrada para la columna de Gravedad
            item_gravedad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # 3. Aplicación de colores según severidad
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

            # 4. Asignación de los elementos a sus respectivas columnas en la fila activa
            self.tabla_dtc.setItem(row_idx, 0, item_codigo)
            self.tabla_dtc.setItem(row_idx, 1, item_categoria)
            self.tabla_dtc.setItem(row_idx, 2, item_gravedad)
            self.tabla_dtc.setItem(row_idx, 3, item_descripcion)
            self.tabla_dtc.setItem(row_idx, 4, item_solucion)
