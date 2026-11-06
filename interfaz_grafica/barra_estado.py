"""
Módulo de la Barra de Estado de Conexión para Blar Plus.

Este módulo define un componente gráfico personalizado (Widget) que
proporciona retroalimentación visual al usuario sobre el estado de la
conexión serie/OBD-II con el vehículo a través de un indicador LED dinámico.

Autor: Estrada Loaiza Rogelio
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class BarraEstadoWidget(QWidget):
    """
    Widget dinámico de la barra de estado que simula un LED indicador.

    Gestión visual del estado de comunicación del hardware mediante colores:
    - Verde (#22c55e): Conexión establecida y activa.
    - Rojo (#ef4444): Equipo desconectado o falla de enlace.
    - Amarillo (#eab308): Proceso de reconexión o búsqueda de puerto.

    Atributos:
        led (QLabel): Componente circular con estilos CSS que actúa como foco LED.
        lbl_mensaje (QLabel): Etiqueta informativa con la descripción textual del estado.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa el widget de la barra de estado y configura su interfaz.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía de Qt.
        """
        super().__init__(parent)
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """
        Ensambla la disposición visual (Layout) interna y los componentes del widget.

        Establece márgenes compactos y alinea horizontalmente el indicador LED
        junto a la etiqueta de texto explicativa.
        """
        # Layout horizontal principal para contener el LED y el mensaje
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # Márgenes reducidos (Izquierda, Arriba, Derecha, Abajo)
        layout.setSpacing(8)  # Espaciado de 8 píxeles entre el LED y el texto

        # 1. Creación del objeto que simulará el indicador LED
        self.led = QLabel()
        self.led.setFixedSize(14, 14)  # Dimensiones fijas de 14x14 píxeles para el círculo

        # Estado inicial por defecto: Desconectado (Color Rojo)
        self._aplicar_estilo_led("#ef4444")

        # 2. Creación del mensaje textual
        self.lbl_mensaje = QLabel("Desconectado")
        self.lbl_mensaje.setStyleSheet("font-weight: 500; color: #333333;")

        # 3. Integración de componentes al layout horizontal
        layout.addWidget(self.led)
        layout.addWidget(self.lbl_mensaje)
        layout.addStretch()  # Empuja los componentes a la izquierda impidiendo que se dispersen

    def _aplicar_estilo_led(self, color_hex: str) -> None:
        """
        Modifica el estilo CSS en línea de la etiqueta LED para simular un foco encendido.

        Args:
            color_hex (str): Código de color hexadecimal para el fondo del LED (ej. '#22c55e').
        """
        # border-radius en 7px (la mitad del ancho de 14px) genera la forma perfectamente circular
        self.led.setStyleSheet(f"""
            background-color: {color_hex};
            border-radius: 7px;
            border: 1px solid rgba(0, 0, 0, 0.25);
        """)

    def actualizar_estado(
        self, conectado: bool, mensaje: str, reintentando: bool = False
    ) -> None:
        """
        Actualiza de forma dinámica el color del LED y la etiqueta textual.

        Args:
            conectado (bool): Indica si la comunicación OBD-II está activa.
            mensaje (str): Descripción detallada a desplegar en la interfaz.
            reintentando (bool): Define si el sistema intenta restablecer la conexión.
        """
        if reintentando:
            color = "#eab308"  # Amarillo para estados intermedios o reintentos
        elif conectado:
            color = "#22c55e"  # Verde para conexión confirmada
        else:
            color = "#ef4444"  # Rojo para estado desconectado

        self._aplicar_estilo_led(color)
        self.lbl_mensaje.setText(mensaje)
