"""
Módulo de Gráficos Técnicos en Tiempo Real para Blar Plus.

Proporciona un widget especializado basado en pyqtgraph para renderizar datos
continuos de sensores vehiculares a alta frecuencia, manteniendo una gestión de memoria
eficiente mediante el uso de un buffer circular.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importacion de deque para la implementacion de buffers circulares con tamaño maximo
from collections import deque
# Importacion de Optional para tipado opcional del widget contenedor
from typing import Optional
# Importacion de clases base para construccion de widgets y layouts
from PySide6.QtWidgets import QWidget, QVBoxLayout
# Importacion de la libreria pyqtgraph especializada en graficado de alto rendimiento
import pyqtgraph as pg

# Desactivacion de suavizado de lineas para maximizar los fotogramas por segundo (FPS)
pg.setConfigOptions(antialias=False)
# Desactivacion del renderizador OpenGL para mantener compatibilidad en Linux/Ubuntu
pg.setConfigOption("useOpenGL", False)


# Clase GraficoTiempoRealWidget para renderizar lecturas de sensores a alta frecuencia
class GraficoTiempoRealWidget(QWidget):
    """
    Widget de gráfico en tiempo real configurado con un buffer circular de 100 muestras.

    Atributos:
        plot_widget (pg.PlotWidget): Lienzo principal de renderizado de pyqtgraph.
        max_puntos (int): Límite superior de lecturas almacenadas simultáneamente en memoria.
        x_data (deque): Colección circular para los índices del eje horizontal.
        y_data (deque): Colección circular para los valores numéricos recibidos del sensor.
        contador_x (int): Secuencia incremental para el eje temporal/muestras.
        curva (pg.PlotDataItem): Elemento gráfico que dibuja la línea continua del sensor.
    """

    # Constructor que inicializa el lienzo de pyqtgraph y las colecciones circulares
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la estructura del lienzo gráfico y la memoria circular.

        Args:
            parent (Optional[QWidget]): Widget contenedor en el esquema de Qt.
        """
        # Invocacion del constructor base de QWidget
        super().__init__(parent)

        # Creacion del layout vertical que contendra el grafico
        layout = QVBoxLayout(self)
        # Eliminacion de margenes alrededor del grafico
        layout.setContentsMargins(0, 0, 0, 0)

        # Instanciacion del widget lienzo principal de pyqtgraph
        self.plot_widget = pg.PlotWidget()
        # Adicion del lienzo gráfico al layout del widget
        layout.addWidget(self.plot_widget)

        # Fondo blanco para el lienzo del grafico
        self.plot_widget.setBackground("w")
        # Habilitacion de cuadrícula en ejes X e Y
        self.plot_widget.showGrid(x=True, y=True)
        # Etiqueta del eje vertical Y
        self.plot_widget.setLabel("left", "Valor del Sensor")
        # Etiqueta del eje horizontal X
        self.plot_widget.setLabel("bottom", "Muestras")
        # Titulo principal superior del grafico
        self.plot_widget.setTitle("Monitoreo en Tiempo Real")

        # Definicion del limite maximo de puntos en pantalla (buffer circular)
        self.max_puntos: int = 100
        # Buffer circular para almacenar los indices del eje X
        self.x_data: deque = deque(maxlen=self.max_puntos)
        # Buffer circular para almacenar los valores del sensor en el eje Y
        self.y_data: deque = deque(maxlen=self.max_puntos)
        # Contador incremental continuo para el eje de muestras
        self.contador_x: int = 0

        # Configuracion del lapiz de dibujo (color azul RGB y grosor 2)
        pen = pg.mkPen(color=(0, 114, 189), width=2)
        # Inicializacion de la linea de curva con marcadores circulares de tamaño 5
        self.curva = self.plot_widget.plot(pen=pen, symbol="o", symbolSize=5)

    # Metodo para actualizar el grafico con una nueva lectura recibida del sensor
    def actualizar_sensor(self, nombre_sensor: str, valor: float) -> None:
        """
        Agrega una nueva lectura al buffer circular y redibuja la curva inmediatamente.

        Args:
            nombre_sensor (str): Identificador técnico del parámetro monitoreado.
            valor (float): Lectura numérica obtenida desde la ECU o simulador.
        """
        # Actualizacion dinamica del titulo del grafico indicando el sensor activo
        self.plot_widget.setTitle(f"Sensor Activo: {nombre_sensor}")

        # Adicion del indice incremental al buffer X
        self.x_data.append(self.contador_x)
        # Adicion de la lectura numerica al buffer Y
        self.y_data.append(valor)
        # Incremento de la secuencia de muestras
        self.contador_x += 1

        # Actualizacion de los datos de la curva convirtiendo los deques a listas de Python
        self.curva.setData(list(self.x_data), list(self.y_data))
