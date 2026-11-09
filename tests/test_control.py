"""
Suite de Pruebas Unitarias Integradas para la Capa de Control y Concurrencia.

Evalúa:
1. El bucle continuo a 10 Hz y detención segura de `TrabajadorOBD`.
2. La captura de errores de conexión inicial en `TrabajadorOBD`.
3. La transformación de cadenas crudas a objetos `DTCDTO` en `ControladorReporte`.
4. La acumulación de reportes en el historial de sesión.

Autor: Erick Polanco Romero
"""

from unittest.mock import MagicMock
import pytest
from pytestqt.qtbot import QtBot

from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO


def test_trabajador_obd_sondeo_continuo_y_detencion(qtbot: QtBot) -> None:
    """
    Verifica que `TrabajadorOBD` emita señales en su bucle continuo a 10 Hz
    y finalice adecuadamente al llamar al método `detener()`.

    Pasos:
    1. Simula un adaptador que retorna True en `conectar()` y una lista DTC en `leer_dtc()`.
    2. Espera asíncronamente la emisión de `datos_recibidos` mediante `qtbot.waitSignal`.
    3. Llama a `detener()` y confirma que el hilo deja de ejecutarse (`isRunning() == False`).
    """
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtc.return_value = ["P0300", "P0171"]

    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=1000) as blocker:
        trabajador.start()

    # Validar que los datos emitidos por el hilo coincidan
    assert blocker.args == [["P0300", "P0171"]]

    # Detener el hilo de forma segura y aseverar que ya no esté activo
    trabajador.detener()
    assert not trabajador.isRunning()


def test_trabajador_obd_falla_conexion_inicial(qtbot: QtBot) -> None:
    """
    Verifica la emisión inmediata de `error_ocurrido` si el adaptador no logra conectarse.

    Pasos:
    1. Configura el mock del adaptador para retornar `False` en `conectar()`.
    2. Intercepta la señal de error.
    3. Confirma el mensaje descriptivo y la posterior detención limpia.
    """
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = False

    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    with qtbot.waitSignal(trabajador.error_ocurrido, timeout=1000) as blocker:
        trabajador.start()

    assert "No se pudo establecer conexión" in blocker.args[0]
    trabajador.detener()


def test_controlador_reporte_procesar_dtcs_raw() -> None:
    """
    Evalúa la transformación de una lista de cadenas crudas DTC a Objetos `DTCDTO`.

    Pasos:
    1. Envía códigos catalogados ("P0300", "P0113") y un código no catalogado ("P9999").
    2. Verifica que se retornen instancias válidas de `DTCDTO`.
    3. Revisa la asignación de campos para el catálogo y para el fallback no catalogado.
    """
    controlador = ControladorReporte()
    dtcs_raw = ["P0300", "P0113", "P9999"]

    dtos = controlador.procesar_dtcs_raw(dtcs_raw)

    assert len(dtos) == 3
    assert isinstance(dtos[0], DTCDTO)

    # Evaluación de código catalogado conocido
    assert dtos[0].codigo == "P0300"
    assert dtos[0].categoria == "Encendido"
    assert dtos[0].gravedad == "Alta"

    # Evaluación de fallback para código no registrado en catálogo
    assert dtos[2].codigo == "P9999"
    assert dtos[2].categoria == "General"
    assert "no catalogado" in dtos[2].descripcion


def test_controlador_reporte_generar_reporte_e_historial() -> None:
    """Verifica la generación de reportes y la acumulación secuencial en memoria."""
    controlador = ControladorReporte()

    reporte1 = controlador.generar_reporte(["P0300"])
    reporte2 = controlador.generar_reporte([])

    historial = controlador.obtener_historial()

    assert reporte1["estado"] == "Crítico"
    assert reporte2["estado"] == "Sin Fallas"
    assert len(historial) == 2
