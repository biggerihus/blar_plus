"""
Módulo de la Barra de Estado de Conexión para Blar Plus.

Implementa un indicador visual estilizado que simula el comportamiento de un LED
para reflejar el estado actual del enlace físico o virtual con la ECU del vehículo.

Autor: Estrada Loaiza Rogelio
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class BarraEstadoWidget(QWidget):
    """
    Widget con indicador LED circular y etiqueta descriptiva de estado.

    Atributos:
        led (QLabel): Componente gráfico estilizado como un LED redondo.
        lbl_mensaje (QLabel): Etiqueta textual con la descripción del estado actual.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la barra de estado y configura su apariencia.

        Args:
            parent (Optional[QWidget]): Widget padre opcional.
        """
        super().__init__(parent)
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Ensambla el diseño horizontal e inserta los componentes del indicador."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self.led = QLabel()
        self.led.setFixedSize(14, 14)
        self._aplicar_estilo_led("#ef4444")

        self.lbl_mensaje = QLabel("Desconectado")
        self.lbl_mensaje.setStyleSheet("font-weight: 500; color: #333333;")

        layout.addWidget(self.led)
        layout.addWidget(self.lbl_mensaje)
        layout.addStretch()

    def _aplicar_estilo_led(self, color_hex: str) -> None:
        """
        Aplica reglas CSS para dar formato de esfera luminosa al indicador.

        Args:
            color_hex (str): Valor hexadecimal del color deseado (ej. '#22c55e').
        """
        self.led.setStyleSheet(f"""
            background-color: {color_hex};
            border-radius: 7px;
            border: 1px solid rgba(0, 0, 0, 0.25);
        """)

    def actualizar_estado(
        self, conectado: bool, mensaje: str, reintentando: bool = False
    ) -> None:
        """
        Actualiza el color del LED y el mensaje descriptivo en pantalla.

        Args:
            conectado (bool): Verdadero si existe conexión activa.
            mensaje (str): Explicación del estado.
            reintentando (bool): Verdadero si se encuentra procesando la reconexión.
        """
        if reintentando:
            color = "#eab308"
        elif conectado:
            color = "#22c55e"
        else:
            color = "#ef4444"

        self._aplicar_estilo_led(color)
        self.lbl_mensaje.setText(mensaje)
