"""
Pruebas unitarias para la capa de Control y Concurrencia (TrabajadorOBD).

Verifica el comportamiento asíncrono y la correcta emisión de señales Qt
utilizando objetos Mock y el fixture `qtbot` de pytest-qt.

Autor: Erick Polanco Romero
"""

from unittest.mock import MagicMock
import pytest
from pytestqt.qtbot import QtBot

from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD


def test_trabajador_obd_emite_datos_correctos(qtbot: QtBot) -> None:
    """
    Prueba el flujo exitoso de lectura OBD.

    Verifica que al conectarse correctamente, el hilo lea los datos del
    adaptador y emita la señal `datos_recibidos` con la lista esperada.
    """
    # 1. Creación del Mock que simula el adaptador de hardware desacoplado
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtcs.return_value = ["P0300", "P0171"]

    # 2. Instanciación de la clase a probar
    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # 3. Intercepción asíncrona de la señal mediante qtbot
    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=1000) as blocker:
        trabajador.start()  # Arranca el hilo secundario

    # 4. Validar que la señal haya sido emitida con el argumento correcto
    assert blocker.args == [["P0300", "P0171"]]

    # 5. Verificar que se llamaron las funciones clave del adaptador
    mock_adaptador.conectar.assert_called_once()
    mock_adaptador.leer_dtcs.assert_called_once()


def test_trabajador_obd_manejo_de_error(qtbot: QtBot) -> None:
    """
    Prueba el manejo de excepciones durante la lectura OBD.

    Verifica que ante una falla de conexión en la capa de hardware,
    el hilo capture la excepción y emita la señal `error_ocurrido`.
    """
    # 1. Configurar Mock para que simule una falla de puerto serie mediante excepción
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtcs.side_effect = ConnectionError("Falla en puerto serie")

    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # 2. Interceptar la señal de error esperada
    with qtbot.waitSignal(trabajador.error_ocurrido, timeout=1000) as blocker:
        trabajador.start()

    # 3. Validar que el mensaje transmitido por la señal contenga el texto original del fallo
    assert "Falla en puerto serie" in blocker.args[0]
