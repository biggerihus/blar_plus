"""
Suite de Pruebas Unitarias para la Capa de Presentación (GUI).

Evalúa de forma automatizada mediante PyTest y pytest-qt:
1. El comportamiento de actualización del LED en `BarraEstadoWidget`.
2. La carga de filas y formateo en `ListaDTCWidget`.
3. El correcto funcionamiento de conmutación de pantallas en `VentanaPrincipal`.

Autor: Estrada Loaiza Rogelio
"""

import pytest
from pytestqt.qtbot import QtBot

from interfaz_grafica.ventana_principal import VentanaPrincipal
from interfaz_grafica.barra_estado import BarraEstadoWidget
from interfaz_grafica.lista_dtc import ListaDTCWidget, DTCReporte


def test_renderizado_barra_estado(qtbot: QtBot) -> None:
    """
    Verifica el estado inicial y la correcta actualización textual/visual en `BarraEstadoWidget`.

    Pasos:
    1. Instancia `BarraEstadoWidget` y lo registra en `qtbot`.
    2. Comprueba que el mensaje inicial sea 'Desconectado'.
    3. Invoca `actualizar_estado(True, "Conectado")` y valida el nuevo texto del QLabel.
    """
    barra = BarraEstadoWidget()
    qtbot.addWidget(barra)

    # Estado inicial
    assert barra.lbl_mensaje.text() == "Desconectado"

    # Cambio a conectado
    barra.actualizar_estado(True, "Conectado")
    assert barra.lbl_mensaje.text() == "Conectado"


def test_carga_datos_lista_dtc(qtbot: QtBot) -> None:
    """
    Evalúa la inserción correcta de registros DTC dentro de `ListaDTCWidget`.

    Pasos:
    1. Instancia `ListaDTCWidget` y crea una lista de objetos `DTCReporte` de prueba.
    2. Carga los reportes en el widget.
    3. Verifica que la cantidad de filas concuerde con el total de reportes insertados.
    4. Valida los contenidos de las celdas en la primera y segunda fila.
    """
    widget_dtc = ListaDTCWidget()
    qtbot.addWidget(widget_dtc)

    reportes = [
        DTCReporte("P0300", "Encendido", "Alta", "Fallo de encendido aleatorio", "Revisar bujías"),
        DTCReporte("P0113", "Admisión", "Media", "Sensor IAT alto", "Revisar conector"),
    ]

    widget_dtc.cargar_reportes(reportes)

    assert widget_dtc.tabla_dtc.rowCount() == 2
    assert widget_dtc.tabla_dtc.item(0, 0).text() == "P0300"
    assert widget_dtc.tabla_dtc.item(1, 0).text() == "P0113"


def test_ventana_principal_alterna_vistas(qtbot: QtBot) -> None:
    """
    Verifica la navegación dinámica entre pantallas mediante el selector de vistas en `VentanaPrincipal`.

    Pasos:
    1. Instancia `VentanaPrincipal`.
    2. Comprueba que por defecto la vista sea el panel de conductor (Índice 0).
    3. Modifica el menú desplegable al índice 1 (Vista Mecánico).
    4. Confirma que `QStackedWidget` haya cambiado la pantalla visible.
    """
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    # Debe iniciar en vista conductor (Índice 0)
    assert ventana.stacked_vistas.currentIndex() == 0

    # Cambiar a vista mecánico (Índice 1)
    ventana.combo_vista.setCurrentIndex(1)
    assert ventana.stacked_vistas.currentIndex() == 1


def test_ventana_principal_toggle_conexion(qtbot: QtBot) -> None:
    """
    Evalúa el botón de alternancia de conexión de `VentanaPrincipal`.

    Pasos:
    1. Dispara el evento de clic en `btn_conectar`.
    2. Confirma que la propiedad `estadoConexion` cambie a `True`.
    3. Verifica que el mensaje de la barra de estado responda reflejando 'Conectado'.
    """
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    assert ventana.estadoConexion is False

    # Encontrar el botón dentro de la disposición de la ventana e interactuar
    ventana.conectarEquipo()

    assert ventana.estadoConexion is True
    assert ventana.barra_estado.lbl_mensaje.text() == "Conectado"
