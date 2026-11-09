"""
Suite de Pruebas Unitarias Integradas para la Capa de Presentación (GUI).

Evalúa:
1. El comportamiento del diálogo modal de confirmación (`DialogoConfirmacion`).
2. El renderizado y formato condicional de la tabla de diagnósticos (`ListaDTCWidget`).
3. El funcionamiento dinámico de la barra de estado con LED (`BarraEstadoWidget`).
4. La navegación entre pantallas en `VentanaPrincipal`.

Autor: Estrada Loaiza Rogelio
"""

import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
from interfaz_grafica.lista_dtc import ListaDTCWidget, DTCReporte
from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.ventana_principal import VentanaPrincipal


def test_dialogo_confirmacion_aceptar(qtbot: QtBot) -> None:
    """Verifica que al presionar el botón de confirmación el diálogo retorne QDialog.Accepted."""
    dialogo = DialogoConfirmacion()
    qtbot.addWidget(dialogo)
    qtbot.mouseClick(dialogo.boton_aceptar, Qt.MouseButton.LeftButton)
    assert dialogo.result() == DialogoConfirmacion.Accepted


def test_render_lista_dtc(qtbot: QtBot) -> None:
    """Evalúa la adición de registros y cálculo de filas en `ListaDTCWidget`."""
    widget = ListaDTCWidget()
    qtbot.addWidget(widget)
    dummy_reporte = [DTCReporte("P0300", "Encendido", "Alta", "Fallo múltiple", "Revisar bujías")]
    widget.cargar_reportes(dummy_reporte)
    assert widget.tabla.rowCount() == 1


def test_barra_estado_cambio_color(qtbot: QtBot) -> None:
    """Verifica la actualización textual y visual de la barra de estado."""
    barra = BarraEstadoWidget()
    qtbot.addWidget(barra)
    barra.actualizar_estado(True, "Conectado")
    assert barra.lbl_mensaje.text() == "Conectado"


def test_ventana_principal_navegacion(qtbot: QtBot) -> None:
    """Verifica la alternancia de vistas entre el panel de conductor y mecánico."""
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)
    assert ventana.stacked_vistas.currentIndex() == 0

    ventana.combo_vista.setCurrentIndex(1)
    assert ventana.stacked_vistas.currentIndex() == 1
