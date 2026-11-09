"""
Módulo de Barra de Estado del Sistema Blar Plus.

Proporciona un widget indicador visual con diodo emisor de luz (LED) y etiqueta
textual para notificar al usuario el estado de conexión con la ECU en tiempo real.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importación de Optional para anotaciones de tipo de widgets padre
from typing import Optional
# Importación del objeto Qt de PySide6 para banderas de alineación
from PySide6.QtCore import Qt
# Importación de componentes base de PySide6 para construir el widget de barra de estado
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
)


# Clase BarraEstadoWidget encargada de mostrar el estado de enlace y mensajes del sistema
class BarraEstadoWidget(QWidget):
    """
    Widget de la barra de estado que incluye un indicador LED de color y texto descriptivo.

    Atributos:
        lbl_led (QLabel): Indicador gráfico circular que simula un LED (Verde/Rojo).
        lbl_mensaje (QLabel): Etiqueta de texto de alto contraste para avisos del sistema.
    """

    # Constructor del widget de barra de estado
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa el widget y compone la interfaz visual de la barra de estado.

        Args:
            parent (Optional[QWidget]): Widget contenedor padre en la jerarquía.
        """
        # Invocación del constructor base de QWidget
        super().__init__(parent)
        # Llamada al método de inicialización de los componentes gráficos
        self.inicializar_interfaz()

    # Método para configurar y ensamblar la interfaz de la barra de estado
    def inicializar_interfaz(self) -> None:
        """Construye la distribución horizontal del indicador LED y la etiqueta de estado."""
        # Creación del layout horizontal principal para la barra de estado
        layout_principal = QHBoxLayout(self)
        # Definición de márgenes reducidos para mantener una barra delgada y elegante
        layout_principal.setContentsMargins(5, 5, 5, 5)
        # Establecimiento de separación entre el indicador LED y el texto
        layout_principal.setSpacing(10)

        # Instanciación de la etiqueta circular que simula el indicador LED
        self.lbl_led = QLabel()
        # Ajuste de dimensión fija cuadrada de 14x14 píxeles para el punto LED
        self.lbl_led.setFixedSize(14, 14)
        # Asignación de estilo inicial desconectado (LED Rojo)
        self.lbl_led.setStyleSheet(
            "background-color: #D9534F; border-radius: 7px; border: 1px solid #A94442;"
        )

        # Instanciación de la etiqueta de texto para los mensajes del sistema
        self.lbl_mensaje = QLabel("Desconectado del vehículo.")
        # Aplicación de estilo de alto contraste para visibilidad sobre fondo oscuro
        self.lbl_mensaje.setStyleSheet(
            "color: #E0E0E0; font-size: 13px; font-weight: bold;"
        )

        # Inserción del indicador LED en el layout horizontal
        layout_principal.addWidget(self.lbl_led)
        # Inserción de la etiqueta de texto con estiramiento elástico
        layout_principal.addWidget(self.lbl_mensaje, stretch=1)

    # Método público para actualizar dinámicamente el LED y el texto
    def actualizar_estado(self, conectado: bool, mensaje: str) -> None:
        """
        Actualiza el color del LED y la descripción textual según el estado de la conexión.

        Args:
            conectado (bool): True si la ECU está conectada, False en caso contrario.
            mensaje (str): Texto descriptivo del evento o estado del sistema.
        """
        # Actualización del texto descriptivo en la etiqueta de mensaje
        self.lbl_mensaje.setText(mensaje)

        # Evaluación de la bandera booleana de conexión
        if conectado:
            # Estilo de LED verde brillante cuando la conexión está activa
            self.lbl_led.setStyleSheet(
                "background-color: #5CB85C; border-radius: 7px; border: 1px solid #4CAE4C;"
            )
            # Resaltado del texto en verde claro de alto contraste
            self.lbl_mensaje.setStyleSheet(
                "color: #5CB85C; font-size: 13px; font-weight: bold;"
            )
        else:
            # Estilo de LED rojo cuando el sistema está desconectado
            self.lbl_led.setStyleSheet(
                "background-color: #D9534F; border-radius: 7px; border: 1px solid #A94442;"
            )
            # Resaltado del texto en rojo/naranja claro de alto contraste
            self.lbl_mensaje.setStyleSheet(
                "color: #D9534F; font-size: 13px; font-weight: bold;"
            )
