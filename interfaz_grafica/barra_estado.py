"""
Módulo de la Barra de Estado de Conexión para Blar Plus.

Implementa un indicador visual estilizado que simula el comportamiento de un LED
para reflejar el estado actual del enlace físico o virtual con la ECU del vehículo.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importacion de Optional para tipado de referencias que pueden ser nulas
from typing import Optional
# Importacion de componentes de la interfaz grafica desde PySide6.QtWidgets
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


# Clase BarraEstadoWidget que representa el indicador LED de conexion
class BarraEstadoWidget(QWidget):
    """
    Widget con indicador LED circular y etiqueta descriptiva de estado.

    Atributos:
        led (QLabel): Componente gráfico estilizado como un LED redondo.
        lbl_mensaje (QLabel): Etiqueta textual con la descripción del estado actual.
    """

    # Inicializador de la clase que recibe el widget padre opcional
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la barra de estado y configura su apariencia.

        Args:
            parent (Optional[QWidget]): Widget padre opcional.
        """
        # Invocacion al constructor de la clase base QWidget
        super().__init__(parent)
        # Llamada al metodo privado para estructurar la interfaz del widget
        self._inicializar_ui()

    # Metodo para construir y organizar los elementos graficos de la barra de estado
    def _inicializar_ui(self) -> None:
        """Ensambla el diseño horizontal e inserta los componentes del indicador."""
        # Creacion del layout horizontal asociado a este widget
        layout = QHBoxLayout(self)
        # Configuracion de margenes exteriores en izquierda, arriba, derecha y abajo
        layout.setContentsMargins(8, 4, 8, 4)
        # Espaciado interno en pixeles entre los widgets agregados
        layout.setSpacing(8)

        # Instanciacion de la etiqueta que funcionara como indicador LED
        self.led = QLabel()
        # Fijado de dimensiones cuadradas de 14x14 pixeles para el LED
        self.led.setFixedSize(14, 14)
        # Aplicacion inicial del color rojo indicando desconexion
        self._aplicar_estilo_led("#ef4444")

        # Instanciacion de la etiqueta de texto con mensaje por defecto
        self.lbl_mensaje = QLabel("Desconectado")
        # Aplicacion de estilo CSS a la etiqueta para peso de fuente y color
        self.lbl_mensaje.setStyleSheet("font-weight: 500; color: #333333;")

        # Insercion del widget LED en el layout horizontal
        layout.addWidget(self.led)
        # Insercion de la etiqueta de mensaje en el layout horizontal
        layout.addWidget(self.lbl_mensaje)
        # Adicion de espacio flexible para empujar los elementos a la izquierda
        layout.addStretch()

    # Metodo para actualizar el estilo visual CSS de la etiqueta LED
    def _aplicar_estilo_led(self, color_hex: str) -> None:
        """
        Aplica reglas CSS para dar formato de esfera luminosa al indicador.

        Args:
            color_hex (str): Valor hexadecimal del color deseado (ej. '#22c55e').
        """
        # Asignacion de la regla CSS que convierte el cuadrado en un circulo de color con borde
        self.led.setStyleSheet(f"""
            background-color: {color_hex};
            border-radius: 7px;
            border: 1px solid rgba(0, 0, 0, 0.25);
        """)

    # Metodo publico para cambiar dinamicamente el estado de la barra
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
        # Evaluacion si el proceso esta reintentando conexion
        if reintentando:
            # Asignacion del color amarillo hexadecimal
            color = "#eab308"
        # Evaluacion si la conexion esta activa
        elif conectado:
            # Asignacion del color verde hexadecimal
            color = "#22c55e"
        # Si no hay conexion activa ni reintento
        else:
            # Asignacion del color rojo hexadecimal
            color = "#ef4444"

        # Aplicacion del nuevo color al indicador LED
        self._aplicar_estilo_led(color)
        # Actualizacion del texto explicativo en la etiqueta de mensaje
        self.lbl_mensaje.setText(mensaje)
