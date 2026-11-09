"""
Módulo de Gráficos Técnicos en Tiempo Real para Blar Plus.

Proporciona un widget especializado basado en pyqtgraph para renderizar datos
continuos de sensores vehiculares a alta frecuencia, manteniendo una gestión de memoria
eficiente mediante el uso de un buffer circular, auto-escalado dinámico y selección multisensores.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación de deque para la implementación de buffers circulares con tamaño máximo
from collections import deque
# Importación de Dict, List, Optional y Tuple para anotaciones de tipo estrictas
from typing import Dict, List, Optional, Tuple, Union
# Importación de componentes de layout, selector y etiquetas de PySide6
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
)
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
    Widget de gráfico en tiempo real configurado con buffer circular de 100 muestras,
    selector de sensores interactivo y cálculo dinámico de Mínimo / Máximo / Actual.

    Atributos:
        plot_widget (pg.PlotWidget): Lienzo principal de renderizado de pyqtgraph.
        combo_sensor (QComboBox): Desplegable interactivo de selección de sensor.
        max_puntos (int): Límite superior de lecturas almacenadas simultáneamente.
        sensores_data (Dict): Diccionario de buffers circulares (x_data, y_data) por sensor.
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

        # Mapa de configuración de sensores soportados: PID, nombre visual, unidad y color RGB
        self.config_sensores: Dict[str, Dict[str, Union[str, Tuple[int, int, int]]]] = {
            "rpm": {"nombre": "RPM del Motor", "unidad": "RPM", "color": (0, 229, 255)},
            "velocidad": {"nombre": "Velocidad Vehicular", "unidad": "km/h", "color": (118, 255, 3)},
            "temperatura": {"nombre": "Temperatura Refrigerante", "unidad": "°C", "color": (255, 214, 0)},
            "carga_motor": {"nombre": "Carga del Motor", "unidad": "%", "color": (255, 128, 0)},
            "posicion_acelerador": {"nombre": "Posición Acelerador", "unidad": "%", "color": (255, 64, 129)},
            "maf": {"nombre": "Flujo de Aire (MAF)", "unidad": "g/s", "color": (179, 136, 255)},
            "sensor_o2": {"nombre": "Sensor de Oxígeno (O2)", "unidad": "V", "color": (0, 230, 118)},
            "iat": {"nombre": "Temp. Aire Admisión", "unidad": "°C", "color": (255, 171, 64)},
            "nivel_combustible": {"nombre": "Nivel Combustible", "unidad": "%", "color": (64, 196, 255)},
            "presion_map": {"nombre": "Presión MAP", "unidad": "kPa", "color": (224, 64, 251)},
        }

        # Sensor actualmente seleccionado para visualización activa en la gráfica
        self.sensor_activo_clave: str = "rpm"

        # Límite máximo de muestras en pantalla por sensor (buffer circular)
        self.max_puntos: int = 100
        # Contador incremental continuo para la escala del eje temporal
        self.contador_x: int = 0

        # Diccionario para almacenar los buffers circulares de datos (x_data, y_data) por cada sensor
        self.sensores_data: Dict[str, Tuple[deque, deque]] = {}

        # Diccionario para almacenar los registros históricos (Mínimo, Máximo) por sensor
        self.estadisticas_sensores: Dict[str, Dict[str, float]] = {}

        # Llamada al método de ensamble visual de la interfaz gráfica
        self.inicializar_interfaz()

    # Método para inicializar el diseño visual y los componentes del gráfico
    def inicializar_interfaz(self) -> None:
        """Configura el selector de sensores, los indicadores Mín/Máx y el lienzo pyqtgraph."""
        # Layout vertical principal del widget gráfico
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(4)

        # Layout horizontal superior para el selector de sensores y panel de resumen
        layout_cabecera = QHBoxLayout()

        # Etiqueta indicadora del selector en blanco de alto contraste
        lbl_selector = QLabel("Sensor Activo:")
        lbl_selector.setStyleSheet("font-weight: bold; color: #FFFFFF; font-size: 11pt;")
        layout_cabecera.addWidget(lbl_selector)

        # Selector desplegable QComboBox para alternar el sensor mostrado en la gráfica
        self.combo_sensor = QComboBox()
        # Estilo QSS con indicador de flecha descendente (▼) en el lado derecho
        self.combo_sensor.setStyleSheet("""
            QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 28px 4px 8px;
                font-weight: bold;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #444444;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #FFFFFF;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #007ACC;
            }
        """)

        # Carga de las opciones de sensores en el desplegable
        for clave, config in self.config_sensores.items():
            self.combo_sensor.addItem(str(config["nombre"]), clave)

        # Conectar el cambio de selección con el método de alternancia de sensor
        self.combo_sensor.currentIndexChanged.connect(self._al_cambiar_sensor_seleccionado)
        layout_cabecera.addWidget(self.combo_sensor)

        # Espaciador horizontal
        layout_cabecera.addStretch()

        # Etiqueta de resumen para desplegar los valores Mín / Máx / Actual
        self.lbl_estadisticas = QLabel("Actual: -- | Mín: -- | Máx: --")
        self.lbl_estadisticas.setStyleSheet(
            "color: #00E5FF; font-weight: bold; font-size: 11pt; background-color: #252525; padding: 4px 10px; border-radius: 4px; border: 1px solid #333333;"
        )
        layout_cabecera.addWidget(self.lbl_estadisticas)

        # Agregar la cabecera al layout principal
        layout_principal.addLayout(layout_cabecera)

        # Instanciación del widget lienzo principal de pyqtgraph
        self.plot_widget = pg.PlotWidget()
        layout_principal.addWidget(self.plot_widget)

        # Establecimiento del fondo oscuro `#1E1E1E` coincidente con el tema visual de Blar Plus
        self.plot_widget.setBackground("#1E1E1E")

        # Habilitación de cuadrícula visible en ejes X e Y con opacidad controlada
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configuración de auto-escalado automático del eje Y para evitar que la gráfica quede plana
        self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis)

        # Estilización de las etiquetas textuales del eje vertical (Y) e inferior (X)
        self.plot_widget.setLabel("left", "Valor del Sensor", color="#FFFFFF", size="10pt")
        self.plot_widget.setLabel("bottom", "Muestras (Tiempo)", color="#FFFFFF", size="10pt")

        # Configuración del color del texto de la escala numérica de los ejes
        self.plot_widget.getAxis("left").setTextPen("#A0A0A0")
        self.plot_widget.getAxis("bottom").setTextPen("#A0A0A0")

        # Creación de la curva única activa de renderizado
        color_inicial = self.config_sensores["rpm"]["color"]
        pen = pg.mkPen(color=color_inicial, width=2)
        self.curva_activa = self.plot_widget.plot(
            pen=pen,
            symbol="o",
            symbolSize=4,
            symbolBrush=color_inicial,
            name="RPM del Motor"
        )

        # Inicialización de la curva con título inicial
        self._actualizar_titulo_grafico("RPM del Motor", 0.0, "RPM")

    # Método slot ejecutado al cambiar la opción en el combo de sensores
    def _al_cambiar_sensor_seleccionado(self, index: int) -> None:
        """
        Cambia el sensor enfocado en la gráfica y ajusta el color y auto-escalado.

        Args:
            index (int): Índice seleccionado en el QComboBox.
        """
        # Recuperar la clave del sensor seleccionado desde los datos del ítem del combo
        self.sensor_activo_clave = self.combo_sensor.currentData()
        config = self.config_sensores.get(self.sensor_activo_clave, self.config_sensores["rpm"])

        # Actualización del color de la pluma y marcador según la paleta del sensor
        color_rgb = config["color"]
        pen = pg.mkPen(color=color_rgb, width=2)
        self.curva_activa.setPen(pen)
        self.curva_activa.setSymbolBrush(color_rgb)

        # Forzar auto-escalado dinámico del Eje Y al cambiar de parámetro
        self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis)

        # Re-renderizar los datos almacenados en el buffer del nuevo sensor activo
        if self.sensor_activo_clave in self.sensores_data:
            buf_x, buf_y = self.sensores_data[self.sensor_activo_clave]
            self.curva_activa.setData(list(buf_x), list(buf_y))
            if buf_y:
                ultimo_val = buf_y[-1]
                self._actualizar_titulo_grafico(str(config["nombre"]), ultimo_val, str(config["unidad"]))
                self._actualizar_etiqueta_estadisticas(self.sensor_activo_clave, ultimo_val)

    # Método para actualizar el título superior de la gráfica
    def _actualizar_titulo_grafico(self, nombre: str, valor: float, unidad: str) -> None:
        """Actualiza la barra de título superior del lienzo pyqtgraph."""
        self.plot_widget.setTitle(
            f'<span style="color: #FFFFFF; font-size: 12pt; font-weight: bold;">'
            f'Monitoreo en Tiempo Real - {nombre}: {valor:.1f} {unidad}</span>'
        )

    # Método para actualizar las estadísticas de Mínimo, Máximo y Valor Actual
    def _actualizar_etiqueta_estadisticas(self, clave_sensor: str, valor_actual: float) -> None:
        """Calcula y despliega los valores de Mínimo, Máximo e Instantáneo del sensor activo."""
        config = self.config_sensores.get(clave_sensor, self.config_sensores["rpm"])
        unidad = config["unidad"]

        # Inicialización de estadísticas si el sensor no tiene registros previos
        if clave_sensor not in self.estadisticas_sensores:
            self.estadisticas_sensores[clave_sensor] = {"min": valor_actual, "max": valor_actual}
        else:
            stats = self.estadisticas_sensores[clave_sensor]
            stats["min"] = min(stats["min"], valor_actual)
            stats["max"] = max(stats["max"], valor_actual)

        min_val = self.estadisticas_sensores[clave_sensor]["min"]
        max_val = self.estadisticas_sensores[clave_sensor]["max"]

        # Asignar texto formateado a la etiqueta superior de resumen
        self.lbl_estadisticas.setText(
            f"Actual: {valor_actual:.1f} {unidad} | Mín: {min_val:.1f} | Máx: {max_val:.1f}"
        )

    # Método receptor flexible compatible con diccionarios o pares de sensor/valor
    def actualizar_grafico(
        self, datos_o_nombre: Union[dict, str, float, int], valor: Optional[float] = None
    ) -> None:
        """
        Slot receptor principal para actualizar los buffers del gráfico en tiempo real.

        Soporta tres firmas de llamada:
        1. `actualizar_grafico(dict_sensores)`: Diccionario completo emitiendo todos los sensores.
        2. `actualizar_grafico("rpm", 1500.0)`: Sensor individual y su valor.
        3. `actualizar_grafico(1500.0)`: Valor numérico directo atribuido al sensor activo.

        Args:
            datos_o_nombre (Union[dict, str, float, int]): Diccionario, nombre o valor numérico directo.
            valor (Optional[float]): Valor numérico si se pasa un sensor individual por nombre.
        """
        # Si se recibe un diccionario completo con lecturas continuas
        if isinstance(datos_o_nombre, dict):
            for clave_sensor, val_num in datos_o_nombre.items():
                self.actualizar_sensor(clave_sensor, float(val_num))
        # Si se pasa el par nombre/valor individual
        elif isinstance(datos_o_nombre, str) and valor is not None:
            self.actualizar_sensor(datos_o_nombre, float(valor))
        # Si se transmite un valor numérico directo sin clave
        elif isinstance(datos_o_nombre, (float, int)):
            self.actualizar_sensor(self.sensor_activo_clave, float(datos_o_nombre))

    # Método para agregar una lectura al buffer circular del sensor indicado
    def actualizar_sensor(self, nombre_sensor: str, valor: float) -> None:
        """
        Agrega una nueva lectura al buffer circular del sensor y redibuja si es el sensor activo.

        Args:
            nombre_sensor (str): Identificador técnico del sensor (ej. 'rpm', 'velocidad').
            valor (float): Lectura numérica obtenida desde la ECU o el simulador.
        """
        # Normalización de la clave del sensor a minúsculas
        clave = nombre_sensor.lower()

        # Inicializar el buffer circular si es la primera lectura registrada
        if clave not in self.sensores_data:
            buf_x = deque(maxlen=self.max_puntos)
            buf_y = deque(maxlen=self.max_puntos)
            self.sensores_data[clave] = (buf_x, buf_y)

        buf_x, buf_y = self.sensores_data[clave]

        # Inserción de la nueva lectura en el buffer circular
        buf_x.append(self.contador_x)
        buf_y.append(float(valor))

        # Incrementar el contador temporal global
        self.contador_x += 1

        # Si el sensor actualizado coincide con el sensor activo en pantalla, redibujar la gráfica
        if clave == self.sensor_activo_clave:
            self.curva_activa.setData(list(buf_x), list(buf_y))
            config = self.config_sensores.get(clave, {"nombre": clave, "unidad": ""})
            self._actualizar_titulo_grafico(str(config["nombre"]), valor, str(config["unidad"]))
            self._actualizar_etiqueta_estadisticas(clave, valor)

    # Método alias de compatibilidad con versiones previas
    def agregar_dato(self, valor: float) -> None:
        """Alias de compatibilidad para agregar lecturas a las RPM por defecto."""
        self.actualizar_sensor("rpm", valor)

    # Método para limpiar todos los trazados y reiniciar buffers
    def limpiar_grafico(self) -> None:
        """Limpia los buffers de datos, estadísticas y resetea las curvas visuales del lienzo."""
        for buf_x, buf_y in self.sensores_data.values():
            buf_x.clear()
            buf_y.clear()

        self.estadisticas_sensores.clear()
        self.contador_x = 0
        self.curva_activa.setData([], [])
        self.lbl_estadisticas.setText("Actual: -- | Mín: -- | Máx: --")
