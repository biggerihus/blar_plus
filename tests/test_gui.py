"""
Suite de Pruebas Unitarias Integradas para la Capa de Presentación (GUI).

Evalúa:
1. El comportamiento del diálogo modal de confirmación (`DialogoConfirmacion`).
2. El renderizado y formato condicional de la tabla de diagnósticos (`ListaDTCWidget`).
3. El funcionamiento dinámico de la barra de estado con LED (`BarraEstadoWidget`).
4. La navegación entre pantallas en `VentanaPrincipal`.

Autor: Estrada Loaiza Rogelio
Capa: Pruebas Unitarias - Interfaz Gráfica (GUI) / Capa 1
"""

# Importacion del marco de pruebas pytest
import pytest
# Importacion de constantes de interaccion de Qt
from PySide6.QtCore import Qt
# Importacion de QtBot para la manipulacion y simulacion de eventos de usuario en widgets
from pytestqt.qtbot import QtBot

# Importacion de los componentes de la interfaz grafica
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
from interfaz_grafica.lista_dtc import ListaDTCWidget, DTCReporte
from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.ventana_principal import VentanaPrincipal


# Prueba para evaluar la respuesta del dialogo modal al presionar el boton confirmar
def test_dialogo_confirmacion_aceptar(qtbot: QtBot) -> None:
    """Verifica que al presionar el botón de confirmación el diálogo retorne QDialog.Accepted."""
    # Instanciacion del dialogo modal de confirmacion
    dialogo = DialogoConfirmacion()
    # Registro del widget en el asistente de pruebas QtBot
    qtbot.addWidget(dialogo)
    # Simulacion del clic izquierdo del raton en el boton de aceptar
    qtbot.mouseClick(dialogo.boton_aceptar, Qt.MouseButton.LeftButton)
    # Verificacion de que el resultado de ejecucion del dialogo sea QDialog.Accepted
    assert dialogo.result() == DialogoConfirmacion.Accepted


# Prueba para validar el correcto cargado y calculo de filas en la tabla ListaDTCWidget
def test_render_lista_dtc(qtbot: QtBot) -> None:
    """Evalúa la adición de registros y cálculo de filas en `ListaDTCWidget`."""
    # Instanciacion del widget de tabla DTC
    widget = ListaDTCWidget()
    # Registro del widget en QtBot
    qtbot.addWidget(widget)
    # Creacion de lista con un objeto de reporte ficticio de prueba
    dummy_reporte = [DTCReporte("P0300", "Encendido", "Alta", "Fallo múltiple", "Revisar bujías")]
    # Carga de la lista en la tabla del widget
    widget.cargar_reportes(dummy_reporte)
    # Verificacion de que el conteo de filas de la tabla sea exactamente 1
    assert widget.tabla.rowCount() == 1


# Prueba para evaluar la actualizacion de texto y mensaje de la BarraEstadoWidget
def test_barra_estado_cambio_color(qtbot: QtBot) -> None:
    """Verifica la actualización textual y visual de la barra de estado."""
    # Instanciacion del widget de la barra de estado
    barra = BarraEstadoWidget()
    # Registro del widget en el entorno de pruebas de QtBot
    qtbot.addWidget(barra)
    # Actualizacion del estado a conectado con mensaje descriptivo
    barra.actualizar_estado(True, "Conectado")
    # Verificacion de que la etiqueta de mensaje muestre el texto actualizado
    assert barra.lbl_mensaje.text() == "Conectado"


# Prueba para validar la conmutacion de vistas entre los paneles de Conductor y Mecanico
def test_ventana_principal_navegacion(qtbot: QtBot) -> None:
    """Verifica la alternancia de vistas entre el panel de conductor y mecánico."""
    # Instanciacion de la ventana principal de la aplicacion
    ventana = VentanaPrincipal()
    # Registro de la ventana principal en QtBot
    qtbot.addWidget(ventana)
    # Comprobacion de que la vista visible inicial sea el indice 0 (Vista Conductor)
    assert ventana.stacked_vistas.currentIndex() == 0

    # Cambiado programatico del indice del desplegable a 1 (Vista Mecanico)
    ventana.combo_vista.setCurrentIndex(1)
    # Verificacion de que la pantalla visible activa en el stacked widget haya cambiado a 1
    assert ventana.stacked_vistas.currentIndex() == 1
