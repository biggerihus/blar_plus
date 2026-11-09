"""
Módulo de Presentación de Diagnósticos DTC para Blar Plus.

Construye una tabla dinámica interactiva encargada de presentar los códigos de falla (DTC),
clasificándolos visualmente con patrones de color condicional en función de su severidad
e integrando opciones de selección por casilla para borrado e inspección individual.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación de tipos genéricos para anotaciones de tipo estrictas
from typing import List, Optional, Union
# Importación del objeto Qt de PySide6 para banderas de alineación y estados de control
from PySide6.QtCore import Qt
# Importación de QColor para asignación cromática de celdas según gravedad
from PySide6.QtGui import QColor
# Importación de componentes de tabla, vistas y disposición de PySide6
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
# Importación del objeto de transferencia de datos (DTO) desde la capa de control
from nucleo_y_controladores.controlador_reporte import DTCDTO


# Clase contenedora de datos para mantener compatibilidad con reportes DTC directos
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

    # Método constructor para instanciar el objeto DTCReporte
    def __init__(
        self,
        codigo: str,
        categoria: str,
        gravedad: str,
        descripcion: str,
        solucion: str,
    ) -> None:
        # Asignación del código de falla estándar
        self.codigo = codigo
        # Asignación de la categoría o subsistema afectado
        self.categoria = categoria
        # Asignación del nivel de gravedad (Alta, Media, Baja)
        self.gravedad = gravedad
        # Asignación de la descripción técnica
        self.descripcion = descripcion
        # Asignación de la solución recomendada
        self.solucion = solucion


# Clase principal ListaDTCWidget para renderizar la tabla de fallas en PySide6
class ListaDTCWidget(QWidget):
    """
    Widget de tabla responsiva e interactiva para la inspección detallada de códigos DTC.

    Atributos:
        tabla (QTableWidget): Componente que despliega la información organizada en 6 columnas.
    """

    # Constructor del widget de lista de diagnósticos
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa el widget y llama a la configuración de la tabla.

        Args:
            parent (Optional[QWidget]): Widget contenedor padre.
        """
        # Invocación del constructor base de QWidget
        super().__init__(parent)
        # Llamada al método de construcción e inicialización de la interfaz gráfica
        self.inicializar_interfaz()

    # Método para inicializar los componentes visuales de la tabla
    def inicializar_interfaz(self) -> None:
        """Configura la estructura de columnas, selección por checkbox y autoajuste de filas."""
        # Creación del layout vertical principal del widget
        layout_principal = QVBoxLayout(self)
        # Eliminación de los márgenes externos del layout para alineación perfecta
        layout_principal.setContentsMargins(0, 0, 0, 0)

        # Instanciación de la tabla QTableWidget
        self.tabla = QTableWidget()
        # Ocultar la cabecera vertical predeterminada de números de fila (1, 2, 3...)
        self.tabla.verticalHeader().setVisible(False)

        # Configurar la tabla en modo de SOLO LECTURA para bloquear edición de texto manual
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Establecimiento de 6 columnas en total
        self.tabla.setColumnCount(6)
        # Asignación de los encabezados textuales de las 6 columnas
        self.tabla.setHorizontalHeaderLabels([
            "Sel.",
            "Código",
            "Categoría",
            "Gravedad",
            "Descripción",
            "Solución",
        ])

        # Habilitar el ajuste automático de texto en líneas múltiples
        self.tabla.setWordWrap(True)
        # Configurar la cabecera vertical para ajustar automáticamente la altura de cada fila al contenido
        self.tabla.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        # Obtención de la cabecera horizontal para aplicar reglas de redimensionamiento
        header = self.tabla.horizontalHeader()
        # Columna 0 (Sel.): Ancho fijo compacto para centrar la casilla de verificación
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 50)

        # Columna 1 (Código): Ajuste según la longitud del código DTC
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        # Columna 2 (Categoría): Ajuste según la longitud de la categoría
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        # Columna 3 (Gravedad): Ajuste según el texto del nivel de gravedad
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # Columna 4 (Descripción): Estiramiento elástico para ocupar el espacio restante
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        # Columna 5 (Solución): Estiramiento elástico para ocupar el espacio restante
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        # Aplicación de hoja de estilos QSS para integrarse al tema oscuro de la aplicación
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                gridline-color: #333333;
                selection-background-color: #007ACC;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #333333;
            }
            QTableWidget::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        # Adición del componente tabla al layout principal del widget
        layout_principal.addWidget(self.tabla)

    # Método para cargar y renderizar la lista de reportes recibida
    def cargar_reportes(self, reportes: List[Union[DTCReporte, DTCDTO]]) -> None:
        """
        Limpia la tabla y carga la lista de reportes aplicando formato de color según la gravedad
        e insertando casillas de verificación seleccionables. Bloquea la modificación del texto en las celdas.

        Args:
            reportes (List[Union[DTCReporte, DTCDTO]]): Colección de fallas a renderizar.
        """
        # Preservar el conjunto de códigos DTC que el usuario ya había seleccionado antes del refresco
        codigos_previos = set(self.obtener_codigos_seleccionados())

        # Reseteo y limpieza de la cantidad de filas existentes en la tabla
        self.tabla.setRowCount(0)
        # Ajuste de la cantidad total de filas según la cantidad de reportes recibidos
        self.tabla.setRowCount(len(reportes))

        # Banderas de lectura estricta para celdas de texto (Permite selección visual pero deshabilita edición)
        banderas_lectura = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

        # Iteración a través de la lista de reportes con índice de fila
        for row_idx, reporte in enumerate(reportes):
            # Creación del ítem para la casilla de verificación CheckBox (Columna 0)
            item_check = QTableWidgetItem()
            # Banderas necesarias para permitir interacción de marcado nativo por el usuario
            item_check.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            
            # Restablecer el estado marcado si el código ya estaba seleccionado por el mecánico
            if reporte.codigo in codigos_previos:
                item_check.setCheckState(Qt.CheckState.Checked)
            else:
                item_check.setCheckState(Qt.CheckState.Unchecked)

            # Alineación centrada para la casilla de verificación
            item_check.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Creación del ítem inmodificable para la columna de Código DTC (Columna 1)
            item_codigo = QTableWidgetItem(reporte.codigo)
            item_codigo.setFlags(banderas_lectura)
            item_codigo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Creación del ítem inmodificable para la columna de Categoría (Columna 2)
            item_categoria = QTableWidgetItem(reporte.categoria)
            item_categoria.setFlags(banderas_lectura)
            item_categoria.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Creación del ítem inmodificable para la columna de Gravedad (Columna 3)
            item_gravedad = QTableWidgetItem(reporte.gravedad)
            item_gravedad.setFlags(banderas_lectura)
            item_gravedad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Creación del ítem inmodificable para la columna de Descripción (Columna 4)
            item_descripcion = QTableWidgetItem(reporte.descripcion)
            item_descripcion.setFlags(banderas_lectura)

            # Creación del ítem inmodificable para la columna de Solución (Columna 5)
            item_solucion = QTableWidgetItem(reporte.solucion)
            item_solucion.setFlags(banderas_lectura)

            # Normalización del texto de gravedad a minúsculas sin espacios
            gravedad_lower = reporte.gravedad.strip().lower()

            # Aplicación de colores para gravedad Alta (Rojo)
            if gravedad_lower == "alta":
                item_gravedad.setBackground(QColor("#f8d7da"))
                item_gravedad.setForeground(QColor("#721c24"))
            # Aplicación de colores para gravedad Media (Amarillo)
            elif gravedad_lower == "media":
                item_gravedad.setBackground(QColor("#fff3cd"))
                item_gravedad.setForeground(QColor("#856404"))
            # Aplicación de colores para gravedad Baja (Verde)
            elif gravedad_lower == "baja":
                item_gravedad.setBackground(QColor("#d4edda"))
                item_gravedad.setForeground(QColor("#155724"))

            # Inserción de la celda de selección en la columna 0
            self.tabla.setItem(row_idx, 0, item_check)
            # Inserción de la celda de código en la columna 1
            self.tabla.setItem(row_idx, 1, item_codigo)
            # Inserción de la celda de categoría en la columna 2
            self.tabla.setItem(row_idx, 2, item_categoria)
            # Inserción de la celda de gravedad en la columna 3
            self.tabla.setItem(row_idx, 3, item_gravedad)
            # Inserción de la celda de descripción en la columna 4
            self.tabla.setItem(row_idx, 4, item_descripcion)
            # Inserción de la celda de solución en la columna 5
            self.tabla.setItem(row_idx, 5, item_solucion)

        # Ajuste dinámico del alto de todas las filas en función del contenido envuelto
        self.tabla.resizeRowsToContents()

    # Método para consultar los códigos seleccionados por el usuario mediante las casillas
    def obtener_codigos_seleccionados(self) -> List[str]:
        """
        Retorna la lista de códigos DTC cuyas casillas de verificación estén marcadas.

        Returns:
            List[str]: Lista con los códigos seleccionados (ej. ['P0300', 'P0171']).
        """
        # Inicialización de la lista contenedora de códigos marcados
        seleccionados: List[str] = []

        # Recorrido fila por fila en la tabla
        for row in range(self.tabla.rowCount()):
            # Obtención del elemento casilla de la columna 0
            item_check = self.tabla.item(row, 0)
            # Verificación de que el ítem existe y se encuentra en estado marcado (Checked)
            if item_check and item_check.checkState() == Qt.CheckState.Checked:
                # Obtención del ítem de código en la columna 1
                item_codigo = self.tabla.item(row, 1)
                # Verificación de validez del ítem e inserción del código textual en la lista
                if item_codigo:
                    seleccionados.append(item_codigo.text())

        # Retorno de la lista final con los códigos seleccionados
        return seleccionados
