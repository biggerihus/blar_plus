"""
Módulo de Gráficos Técnicos en Tiempo Real para Blar Plus.

Proporciona un widget especializado basado en pyqtgraph para renderizar datos
continuos de sensores vehiculares a alta frecuencia, manteniendo una gestión de memoria
eficiente mediante el uso de un buffer circular y soporte multicanal en tema oscuro.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación de deque para la implementación de buffers circulares con tamaño máximo
from collections import deque
# Importación de Dict, Optional y Tuple para anotaciones de tipo estrictas
from typing import Dict, Optional, Tuple
# Importación de QWidget y QVBoxLayout de PySide6 para la estructura del contenedor
from PySide6.QtWidgets import QWidget, QVBoxLayout
# Importación de QColor para la definición de colores de alta visibilidad
from PySide6.QtGui import QColor
# Importación de la librería pyqtgraph especializada en graficado de alto rendimiento
import pyqtgraph as pg

# Desactivación de suavizado de líneas para maximizar los fotogramas por segundo (FPS)
pg.setConfigOptions(antialias=False)
# Desactivación del renderizador OpenGL para mantener compatibilidad en Linux/Ubuntu
pg.setConfigOption("useOpenGL", False)


# Clase GraficoTiempoRealWidget para renderizar lecturas de sensores a alta frecuencia
class GraficoTiempoRealWidget(QWidget):
    """
    Widget de gráfico en tiempo real configurado con buffer circular de 100 muestras.

    Atributos:
        plot_widget (pg.PlotWidget): Lienzo principal de renderizado de pyqtgraph.
        max_puntos (int): Límite superior de lecturas almacenadas simultáneamente en memoria.
        sensores_data (Dict): Diccionario de buffers circulares (x_data, y_data) por sensor.
        curvas (Dict): Diccionario de objetos de trazado PlotDataItem por sensor.
        colores_disponibles (List): Paleta de colores de alto contraste para múltiples curvas.
        contador_x (int): Secuencia incremental para el eje temporal/muestras.
    """

    # Constructor que inicializa el lienzo de pyqtgraph y las colecciones circulares
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la estructura del lienzo gráfico y la memoria circular.

        Args:
            parent (Optional[QWidget]): Widget contenedor en el esquema de Qt.
        """
        # Invocación del constructor base de QWidget
        super().__init__(parent)

        # Creación del layout vertical que contendrá el gráfico
        layout = QVBoxLayout(self)
        # Eliminación de márgenes alrededor del gráfico para ocupar todo el espacio
        layout.setContentsMargins(0, 0, 0, 0)

        # Instanciación del widget lienzo principal de pyqtgraph
        self.plot_widget = pg.PlotWidget()
        # Adición del lienzo gráfico al layout del widget
        layout.addWidget(self.plot_widget)

        # Establecimiento de fondo oscuro `#1E1E1E` coincidente con el tema visual de Blar Plus
        self.plot_widget.setBackground("#1E1E1E")

        # Habilitación de cuadrícula visible en ejes X e Y con opacidad controlada
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configuración del título principal superior con tipografía blanca y en negrita
        self.plot_widget.setTitle(
            '<span style="color: #FFFFFF; font-size: 13pt; font-weight: bold;">Monitoreo de Sensores en Tiempo Real</span>'
        )

        # Estilización de las etiquetas textuales del eje vertical (Y)
        self.plot_widget.setLabel("left", "Valor del Sensor", color="#FFFFFF", size="11pt")
        # Estilización de las etiquetas textuales del eje horizontal (X)
        self.plot_widget.setLabel("bottom", "Muestras (Tiempo)", color="#FFFFFF", size="11pt")

        # Configuración del color de fuente y pluma de los ejes numéricos (blanco/gris claro)
        eje_izq = self.plot_widget.getAxis("left")
        # Ajuste de color del texto de la escala vertical
        eje_izq.setTextPen("#A0A0A0")

        eje_inf = self.plot_widget.getAxis("bottom")
        # Ajuste de color del texto de la escala horizontal
        eje_inf.setTextPen("#A0A0A0")

        # Definición del límite máximo de puntos en pantalla por sensor (buffer circular)
        self.max_puntos: int = 100
        # Contador incremental continuo para la escala del eje temporal/muestras
        self.contador_x: int = 0

        # Diccionario para almacenar los buffers circulares de datos (x_data, y_data) por cada sensor
        self.sensores_data: Dict[str, Tuple[deque, deque]] = {}
        # Diccionario para almacenar las curvas de trazado PlotDataItem por cada sensor
        self.curvas: Dict[str, pg.PlotDataItem] = {}

        # Paleta de colores de alto contraste para identificar múltiples sensores en la misma gráfica
        self.paleta_colores = [
            (0, 229, 255),    # Cyan brillante (Velocidad / RPM principal)
            (255, 214, 0),    # Amarillo (Temperatura)
            (118, 255, 3),    # Verde neón (Voltaje / Carga)
            (255, 64, 129),   # Rosa neón (Presión)
            (179, 136, 255),  # Púrpura claro (Otros sensores)
        ]

        # Leyenda integrada en la esquina superior derecha de la gráfica
        self.leyenda = self.plot_widget.addLegend(offset=(-10, 10))
        # Estilización transparente con texto blanco para la leyenda
        self.leyenda.setBrush(pg.mkBrush(30, 30, 30, 180))
        self.leyenda.setPen(pg.mkPen("#444444"))

    # Método para actualizar o registrar la curva de un sensor dinámicamente
    def actualizar_sensor(self, nombre_sensor: str, valor: float) -> None:
        """
        Agrega una nueva lectura al buffer circular y redibuja la curva correspondiente.

        Args:
            nombre_sensor (str): Identificador técnico del parámetro monitoreado (ej. 'RPM', 'Velocidad').
            valor (float): Lectura numérica obtenida desde la ECU o simulador.
        """
        # Comprobar si el sensor ya tiene un buffer y una curva inicializados
        if nombre_sensor not in self.sensores_data:
            # Creación del buffer circular X (índices temporales)
            buf_x = deque(maxlen=self.max_puntos)
            # Creación del buffer circular Y (valores numéricos recibidos)
            buf_y = deque(maxlen=self.max_puntos)
            # Almacenamiento de los buffers en el diccionario de sensores
            self.sensores_data[nombre_sensor] = (buf_x, buf_y)

            # Selección de color según la cantidad de curvas creadas
            idx_color = len(self.curvas) % len(self.paleta_colores)
            color_rgb = self.paleta_colores[idx_color]

            # Configuración del lápiz de línea sólida con grosor 2
            pen = pg.mkPen(color=color_rgb, width=2)

            # Creación e inserción de la curva de trazado con marcadores circulares
            nueva_curva = self.plot_widget.plot(
                pen=pen,
                symbol="o",
                symbolSize=4,
                symbolBrush=color_rgb,
                name=nombre_sensor
            )
            # Guardado de la instancia de la curva
            self.curvas[nombre_sensor] = nueva_curva

        # Extracción de los buffers circulares del sensor activo
        buf_x, buf_y = self.sensores_data[nombre_sensor]

        # Adición del índice incremental actual al buffer X
        buf_x.append(self.contador_x)
        # Adición de la lectura numérica del sensor al buffer Y
        buf_y.append(float(valor))

        # Actualización de la curva convirtiendo los deques a listas nativas de Python
        self.curvas[nombre_sensor].setData(list(buf_x), list(buf_y))

        # Incremento del contador global de muestras
        self.contador_x += 1

        # Actualización dinámica del título del gráfico con el último sensor registrado
        self.plot_widget.setTitle(
            f'<span style="color: #FFFFFF; font-size: 13pt; font-weight: bold;">Monitoreo en Tiempo Real - {nombre_sensor}: {valor:.1f}</span>'
        )

    # Método para limpiar todos los trazados y reiniciar buffers
    def limpiar_grafico(self) -> None:
        """Limpia los buffers de datos y elimina las curvas visuales del lienzo."""
        # Limpieza de todos los pares de buffers
        for buf_x, buf_y in self.sensores_data.values():
            buf_x.clear()
            buf_y.clear()

        # Reseteo del contador incremental temporal
        self.contador_x = 0

        # Reinicio de los datos renderizados en cada curva existente
        for curva in self.curvas.values():
            curva.setData([], [])
