# tests/test_gui.py 
import pytest 
from PySide6.QtCore import Qt 
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion 
from interfaz_grafica.lista_dtc import ListaDTCWidget 
from capa_de_datos.modelo_reporte import DTCReporte 
 
def test_dialogo_confirmacion_aceptar(qtbot): 
    dialogo = DialogoConfirmacion() 
    qtbot.addWidget(dialogo) 
    qtbot.mouseClick(dialogo.boton_aceptar, Qt.MouseButton.LeftButton) 
    assert dialogo.result() == DialogoConfirmacion.Accepted 
 
def test_render_lista_dtc(qtbot): 
    widget = ListaDTCWidget() 
    qtbot.addWidget(widget) 
    dummy_reporte = [DTCReporte("P0300", "Fallo Múltiple", "Powertrain", "Alta", "Bujías")] 
    widget.cargar_reportes(dummy_reporte) 
    assert widget.tabla.rowCount() == 1