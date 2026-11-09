"""
Módulo de Diálogo Modal de Confirmación para Blar Plus.

Este módulo implementa una ventana modal de seguridad (QDialog) que interrumpe
el flujo principal para solicitar la confirmación explícita del usuario antes de
ejecutar operaciones críticas en el vehículo, tales como la depuración o borrado
de la memoria de códigos de falla (DTC) de la ECU.

Autor: Estrada Loaiza Rogelio
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QStyle,
    QWidget,
)


class DialogoConfirmacion(QDialog):
    """
    Diálogo modal de advertencia de seguridad para la confirmación de acciones destructivas.

    Bloquea la interacción con la ventana principal hasta que el usuario elija
    aceptar o rechazar la acción propuesta.

    Atributos:
        boton_aceptar (QPushButton): Botón que confirma la acción y emite QDialog.Accepted.
        boton_cancelar (QPushButton): Botón que aborta la operación y emite QDialog.Rejected.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Inicializa la ventana modal y configura la disposición de sus componentes visuales.

        Args:
            parent (Optional[QWidget]): Widget padre opcional en la jerarquía de Qt.
        """
        super().__init__(parent)
        self.setWindowTitle("Advertencia - Borrado de Códigos")
        self.setModal(True)
        self.resize(420, 200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        mensaje_layout = QHBoxLayout()
        mensaje_layout.setSpacing(15)

        icono_label = QLabel()
        icono = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        icono_label.setPixmap(icono.pixmap(48, 48))
        mensaje_layout.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)

        texto_advertencia = QLabel(
            "<b>¡Advertencia de Seguridad!</b><br><br>"
            "Está a punto de borrar los códigos de diagnóstico almacenados "
            "en la memoria del vehículo. Esta acción es permanente y eliminará "
            "el historial de fallas registradas.<br><br>"
            "¿Desea continuar con el borrado?"
        )
        texto_advertencia.setWordWrap(True)
        mensaje_layout.addWidget(texto_advertencia, 1)
        layout.addLayout(mensaje_layout)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(linea)

        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_aceptar = QPushButton("Confirmar")

        self.boton_aceptar.setStyleSheet(
            "background-color: #d9534f; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;"
        )
        self.boton_cancelar.setStyleSheet("padding: 6px 14px; border-radius: 4px;")

        botones_layout.addWidget(self.boton_cancelar)
        botones_layout.addWidget(self.boton_aceptar)
        layout.addLayout(botones_layout)

        self.boton_aceptar.clicked.connect(self.accept)
        self.boton_cancelar.clicked.connect(self.reject)
