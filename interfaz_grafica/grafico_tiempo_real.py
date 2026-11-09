"""
Módulo de Gráficos Técnicos en Tiempo Real para Blar Plus.

Proporciona un widget especializado basado en pyqtgraph para renderizar datos
continuos de sensores vehiculares a alta frecuencia, manteniendo una gestión de memoria
eficiente mediante el uso de un buffer circular.

Autor: Estrada Loaiza Rogelio
"""

from collections import deque
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

pg.setConfigOptions(antialias=False)
pg.setConfigOption("useOpenGL", False)


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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la estructura del lienzo gráfico y la memoria circular.

        Args:
            parent (Optional[QWidget]): Widget contenedor en el esquema de Qt.
        """
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("left", "Valor del Sensor")
        self.plot_widget.setLabel("bottom", "Muestras")
        self.plot_widget.setTitle("Monitoreo en Tiempo Real")

        self.max_puntos: int = 100
        self.x_data: deque = deque(maxlen=self.max_puntos)
        self.y_data: deque = deque(maxlen=self.max_puntos)
        self.contador_x: int = 0

        pen = pg.mkPen(color=(0, 114, 189), width=2)
        self.curva = self.plot_widget.plot(pen=pen, symbol="o", symbolSize=5)

    def actualizar_sensor(self, nombre_sensor: str, valor: float) -> None:
        """
        Agrega una nueva lectura al buffer circular y redibuja la curva inmediatamente.

        Args:
            nombre_sensor (str): Identificador técnico del parámetro monitoreado.
            valor (float): Lectura numérica obtenida desde la ECU o simulador.
        """
        self.plot_widget.setTitle(f"Sensor Activo: {nombre_sensor}")

        self.x_data.append(self.contador_x)
        self.y_data.append(valor)
        self.contador_x += 1

        self.curva.setData(list(self.x_data), list(self.y_data))
