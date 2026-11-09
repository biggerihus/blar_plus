"""
Suite de Pruebas Unitarias Integradas para la Capa de Presentación (GUI).

Evalúa:
1. El comportamiento del diálogo modal de confirmación (`DialogoConfirmacion`).
2. El renderizado y conteo de filas en la tabla de diagnósticos (`ListaDTCWidget`).
3. El funcionamiento dinámico de la barra de estado (`BarraEstadoWidget`).
4. La navegación entre pantallas en `VentanaPrincipal`.

Autor: Estrada Loaiza Rogelio
Capa: Pruebas Unitarias - Interfaz Gráfica (GUI) / Capa 1
"""

# Importación del marco de pruebas pytest
import pytest
# Importación de constantes de Qt
from PySide6.QtCore import Qt
# Importación de QtBot para la simulación de eventos en widgets PySide6
from pytestqt.qtbot import QtBot

# Importación de componentes de la interfaz gráfica
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
from interfaz_grafica.lista_dtc import ListaDTCWidget, DTCReporte
from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.ventana_principal import VentanaPrincipal


# Prueba para evaluar la respuesta del diálogo modal de confirmación
def test_dialogo_confirmacion_aceptar(qtbot: QtBot) -> None:
    """Verifica que al presionar el botón de confirmación el diálogo retorne QDialog.Accepted."""
    # Instanciación del diálogo modal
    dialogo = DialogoConfirmacion()
    # Registro del widget en el asistente QtBot
    qtbot.addWidget(dialogo)
    # Simulación de clic en el botón aceptar
    qtbot.mouseClick(dialogo.boton_aceptar, Qt.MouseButton.LeftButton)
    # Verificación del resultado retornado por el diálogo modal
    assert dialogo.result() == DialogoConfirmacion.Accepted


# Prueba para validar el cargado y renderizado de filas en la tabla ListaDTCWidget
def test_render_lista_dtc(qtbot: QtBot) -> None:
    """Evalúa la adición de registros y el cálculo de filas en `ListaDTCWidget`."""
    # Instanciación del widget de la tabla DTC
    widget = ListaDTCWidget()
    # Registro del widget en QtBot
    qtbot.addWidget(widget)

    # Creación de objeto de reporte de prueba
    dummy_reporte = [DTCReporte("P0300", "Encendido", "Alta", "Fallo múltiple", "Revisar bujías")]
    # Carga de la lista en la tabla
    widget.cargar_reportes(dummy_reporte)

    # Verificación de que la tabla contenga exactamente 1 fila cargada
    assert widget.tabla.rowCount() == 1


# Prueba para evaluar la actualización visual de la barra de estado
def test_barra_estado_cambio_color(qtbot: QtBot) -> None:
    """Verifica la actualización textual del mensaje en la barra de estado."""
    # Instanciación de la barra de estado
    barra = BarraEstadoWidget()
    qtbot.addWidget(barra)

    # Actualización de estado a conectado
    barra.actualizar_estado(True, "Conectado")
    # Verificación del texto desplegado en la etiqueta
    assert barra.lbl_mensaje.text() == "Conectado"


# Prueba para validar la conmutación de vistas en VentanaPrincipal
def test_ventana_principal_navegacion(qtbot: QtBot) -> None:
    """Verifica la alternancia entre la vista de Conductor (0) y Mecánico (1)."""
    # Instanciación de la ventana principal
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    # Verificación de que la vista inicial sea la del Conductor (Índice 0)
    assert ventana.stacked_vistas.currentIndex() == 0

    # Cambio del selector desplegable a la Vista Mecánico (Índice 1)
    ventana.combo_vista.setCurrentIndex(1)
    # Verificación de que la pantalla activa en QStackedWidget haya cambiado a 1
    assert ventana.stacked_vistas.currentIndex() == 1
