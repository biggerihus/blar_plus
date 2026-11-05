"""
Pruebas unitarias integradas para la capa de Control y Concurrencia.

Este módulo evalúa:
1. El comportamiento asíncrono y emisión de señales Qt de `TrabajadorOBD`.
2. El manejo de excepciones de hardware dentro del hilo secundario.
3. La lógica de negocio y estructuración de datos en `ControladorReporte`.

Dependencias de prueba:
- `unittest.mock.MagicMock`: Simulación desacoplada del contrato `IAdaptadorOBD`.
- `pytestqt.qtbot.QtBot`: Intercepción asíncrona de señales Qt sin bloqueo de interfaz.

Autor: Erick Polanco Romero
"""

from unittest.mock import MagicMock
import pytest
from pytestqt.qtbot import QtBot

from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
from nucleo_y_controladores.controlador_reporte import ControladorReporte


def test_trabajador_obd_emite_datos_correctos(qtbot: QtBot) -> None:
    """
    Verifica la transmisión exitosa de datos DTC mediante señales Qt en un hilo secundario.

    Pasos de la prueba:
    1. Configura un mock de `IAdaptadorOBD` para simular lectura exitosa de códigos DTC.
    2. Instancia `TrabajadorOBD` asociando el adaptador mock.
    3. Intercepta la señal `datos_recibidos` mediante el gestor de contexto `qtbot.waitSignal`.
    4. Inicia la ejecución asíncrona del hilo (`.start()`).
    5. Asevera que los datos emitidos por la señal correspondan a la lista esperada.
    """
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtc.return_value = ["P0300", "P0171"]

    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=1000) as blocker:
        trabajador.start()

    assert blocker.args == [["P0300", "P0171"]]
    mock_adaptador.conectar.assert_called_once()
    mock_adaptador.leer_dtc.assert_called_once()


def test_trabajador_obd_manejo_de_error(qtbot: QtBot) -> None:
    """
    Verifica la captura y notificación de excepciones de hardware en el hilo secundario.

    Pasos de la prueba:
    1. Configura el mock del adaptador para lanzar un `ConnectionError` durante la lectura.
    2. Intercepta la emisión de la señal `error_ocurrido`.
    3. Asevera que el mensaje transmitido por la señal contenga el detalle original de la excepción.
    """
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtc.side_effect = ConnectionError("Falla en puerto serie")

    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    with qtbot.waitSignal(trabajador.error_ocurrido, timeout=1000) as blocker:
        trabajador.start()

    assert "Falla en puerto serie" in blocker.args[0]


def test_controlador_reporte_generar_reporte() -> None:
    """
    Evalúa la correcta estructuración y cálculo de métricas en `ControladorReporte`.

    Pasos de la prueba:
    1. Instancia `ControladorReporte`.
    2. Genera un reporte enviando una lista de fallas de prueba.
    3. Valida el conteo total de fallas, la coherencia de los códigos y la severidad asignada.
    """
    controlador = ControladorReporte()
    dtcs_prueba = ["P0300", "P0171"]

    reporte = controlador.generar_reporte(dtcs_prueba)

    assert reporte["total_fallas"] == 2
    assert reporte["codigos"] == dtcs_prueba
    assert reporte["estado"] == "Crítico"


def test_controlador_reporte_historial() -> None:
    """
    Verifica la persistencia y acumulación ordenada de diagnósticos en el historial.

    Pasos de la prueba:
    1. Genera dos reportes consecutivos (uno con fallas y otro limpio).
    2. Obtiene el historial acumulado.
    3. Comprueba el total de registros guardados y el estado correspondiente de cada uno.
    """
    controlador = ControladorReporte()

    controlador.generar_reporte(["P0300"])
    controlador.generar_reporte([])

    historial = controlador.obtener_historial()

    assert len(historial) == 2
    assert historial[0]["estado"] == "Crítico"
    assert historial[1]["estado"] == "Sin Fallas"
