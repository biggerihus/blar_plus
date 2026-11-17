"""
Módulo de Diálogo Modal de Confirmación para Blar Plus.

Este módulo implementa una ventana modal de seguridad (QDialog) que interrumpe
el flujo principal para solicitar la confirmación explícita del usuario antes de
ejecutar operaciones críticas en el vehículo, tales como la depuración o borrado
de la memoria de códigos de falla (DTC) de la ECU mediante el Servicio 04 OBD-II.

Autor: Estrada Loaiza Rogelio
Capa: Interfaz Gráfica (GUI) / Capa 1
"""

# Importacion de Optional para tipado del contenedor padre
from typing import Optional
# Importacion de constantes de alineacion y formato desde PySide6.QtCore
from PySide6.QtCore import Qt
# Importacion de componentes de cuadros de dialogo, botones y layouts desde PySide6.QtWidgets
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStyle,
    QWidget,
    QLayout,
)


# Clase DialogoConfirmacion que hereda de QDialog para mostrar la advertencia modal
class DialogoConfirmacion(QDialog):
    """
    Diálogo modal de advertencia de seguridad para la confirmación de acciones destructivas.

    Bloquea la interacción con la ventana principal hasta que el usuario elija
    aceptar o rechazar la acción propuesta, informando las condiciones estándar OBD-II.

    Atributos:
        boton_aceptar (QPushButton): Botón que confirma la acción y emite QDialog.Accepted.
        boton_cancelar (QPushButton): Botón que aborta la operación y emite QDialog.Rejected.
    """

    # Constructor de la ventana modal que configura componentes y dimensiones
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        motor_encendido: bool = False,
        hay_seleccion_parcial: bool = False,
    ) -> None:
        """
        Inicializa la ventana modal y configura la disposición de sus componentes visuales.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía de Qt.
            motor_encendido (bool): True si las RPM actuales son mayores a 0.
            hay_seleccion_parcial (bool): True si el usuario marcó casillas individuales.
        """
        # Invocacion del constructor base de QDialog
        super().__init__(parent)
        # Definicion del titulo de la ventana en la barra superior
        self.setWindowTitle("Advertencia - Borrado de Códigos (Modo 04)")
        # Activacion del modo modal para bloquear la ventana principal
        self.setModal(True)
        # Ajuste de ancho mínimo a 480 píxeles permitiendo que la altura crezca dinámicamente sin recortes
        self.setMinimumWidth(480)

        # Creacion del layout vertical principal del dialogo
        layout = QVBoxLayout(self)
        # Configuracion de margenes interiores en pixeles
        layout.setContentsMargins(20, 20, 20, 20)
        # Configuracion de espaciado vertical entre elementos
        layout.setSpacing(15)

        # Aplicación de restricción de tamaño para que el QDialog se expanda automáticamente según el texto
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        # Layout horizontal para agrupar el icono de advertencia y el mensaje
        mensaje_layout = QHBoxLayout()
        # Espaciado horizontal entre icono y texto
        mensaje_layout.setSpacing(15)

        # Instanciacion de la etiqueta receptora del icono
        icono_label = QLabel()
        # Obtencion del icono estandar de advertencia del sistema Qt
        icono = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        # Escalado del icono a una imagen de 48x48 pixeles
        icono_label.setPixmap(icono.pixmap(48, 48))
        # Insercion del icono alineado a la parte superior del contenedor
        mensaje_layout.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Construccion dinamica de avisos tecnicos segun estado del vehiculo y seleccion
        avisos_extra = ""
        if hay_seleccion_parcial:
            avisos_extra += (
                "<br><br><span style='color: #F0AD4E;'><b>Nota de Estándar SAE J1979:</b> "
                "En vehículos reales, el Servicio 04 OBD-II borra <b>toda la memoria de fallas</b> "
                "de la ECU de forma global, independientemente de las casillas marcadas.</span>"
            )

        if motor_encendido:
            avisos_extra += (
                "<br><br><span style='color: #FF6B6B;'><b>⚠️ Motor en Marcha Detectado:</b> "
                "La mayoría de las ECUs rechazan el borrado con el motor encendido. Se recomienda "
                "apagar el motor y dejar únicamente el switch en posición <b>ON (KOEO)</b>.</span>"
            )

        # Instanciacion de la etiqueta con el mensaje de advertencia redactado en HTML
        texto_advertencia = QLabel(
            "<b>¡Advertencia de Seguridad!</b><br><br>"
            "Está a punto de enviar la orden de borrado (Servicio 04) a la ECU del vehículo. "
            "Esta acción es permanente, eliminará el historial de fallas, los datos congelados "
            "(<i>Freeze Frame</i>) y reiniciará los monitores de emisiones."
            f"{avisos_extra}<br><br>"
            "¿Desea continuar con el borrado?"
        )
        # Habilitacion de ajuste de texto automatico en multiples lineas
        texto_advertencia.setWordWrap(True)
        # Insercion del texto en el layout asignandole factor de estiramiento 1
        mensaje_layout.addWidget(texto_advertencia, 1)
        # Adicion del layout de mensaje al layout principal vertical
        layout.addLayout(mensaje_layout)

        # Instanciacion de una linea divisora horizontal
        linea = QFrame()
        # Definicion de forma de linea horizontal
        linea.setFrameShape(QFrame.Shape.HLine)
        # Aplicacion de sombra hundida para efecto visual
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        # Insercion de la linea divisora en el layout principal
        layout.addWidget(linea)

        # Layout horizontal para organizar los botones de accion en la parte inferior
        botones_layout = QHBoxLayout()
        # Espaciador flexible para empujar los botones hacia la derecha
        botones_layout.addStretch()

        # Instanciacion del boton Cancelar
        self.boton_cancelar = QPushButton("Cancelar")
        # Instanciacion del boton Confirmar
        self.boton_aceptar = QPushButton("Confirmar Borrado")

        # Aplicacion de estilo CSS rojo de advertencia al boton aceptar
        self.boton_aceptar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;"
        )
        # Aplicacion de estilo CSS estandar al boton cancelar
        self.boton_cancelar.setStyleSheet("padding: 6px 14px; border-radius: 4px;")

        # Insercion del boton cancelar en el layout de botones
        botones_layout.addWidget(self.boton_cancelar)
        # Insercion del boton aceptar en el layout de botones
        botones_layout.addWidget(self.boton_aceptar)
        # Adicion del layout de botones al layout vertical principal
        layout.addLayout(botones_layout)

        # Conexion del evento clic del boton aceptar con el slot accept de QDialog
        self.boton_aceptar.clicked.connect(self.accept)
        # Conexion del evento clic del boton cancelar con el slot reject de QDialog
        self.boton_cancelar.clicked.connect(self.reject)
