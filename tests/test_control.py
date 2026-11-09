"""
Suite de Pruebas Unitarias Integradas para la Capa de Control y Concurrencia.

Evalúa:
1. El sondeo continuo a 10 Hz y detención limpia en `TrabajadorOBD`.
2. La captura y emisión de errores al fallar la conexión inicial en `TrabajadorOBD`.
3. La transformación de cadenas crudas a objetos `DTCDTO` en `ControladorReporte`.
4. La acumulación de reportes en el historial de sesión.

Autor: Erick Polanco Romero
Capa: Pruebas Unitarias - Núcleo y Controladores / Capa 2
"""

# Importación de MagicMock para simular la interfaz de hardware
from unittest.mock import MagicMock
# Importación del marco de pruebas pytest
import pytest
# Importación de QtBot para interactuar con hilos y señales asíncronas de PySide6
from pytestqt.qtbot import QtBot

# Importación de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
# Importación del trabajador asíncrono OBD
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
# Importación del controlador de reportes y el DTO
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO


# Prueba para verificar el bucle asíncrono y la detención limpia del hilo de control
def test_trabajador_obd_sondeo_continuo_y_detencion(qtbot: QtBot) -> None:
    """
    Verifica que `TrabajadorOBD` active el sondeo, emita señales a 10 Hz
    y finalice adecuadamente al invocar `detener()`.
    """
    # Instanciación del mock del adaptador de hardware
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    # Configuración de respuestas simuladas exitosas
    mock_adaptador.conectar.return_value = True
    mock_adaptador.leer_dtc.return_value = ["P0300", "P0171"]
    mock_adaptador.leer_pid.return_value = 100.0

    # Instanciación del trabajador con el adaptador inyectado
    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # Intercepción de la señal datos_recibidos con tiempo límite de 1500 ms
    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=1500) as blocker:
        # Activar el sondeo explícitamente e iniciar el hilo secundario
        trabajador.iniciar_sondeo()
        trabajador.start()

    # Verificación de que los datos emitidos por la señal coincidan con la lista esperada
    assert blocker.args == [["P0300", "P0171"]]

    # Invocación de la detención segura del hilo
    trabajador.detener()
    # Aserción de que el hilo ha finalizado su ejecución
    assert not trabajador.isRunning()


# Prueba para verificar el manejo de errores ante fallo de conexión inicial
def test_trabajador_obd_falla_conexion_inicial(qtbot: QtBot) -> None:
    """Verifica la emisión inmediata de `error_ocurrido` cuando `conectar()` devuelve False."""
    # Instanciación del mock simulando rechazo de conexión
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    mock_adaptador.conectado = False
    mock_adaptador.conectar.return_value = False

    # Instanciación de TrabajadorOBD
    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # Captura de la señal error_ocurrido
    with qtbot.waitSignal(trabajador.error_ocurrido, timeout=1500) as blocker:
        # Intentar iniciar el sondeo
        trabajador.iniciar_sondeo()

    # Verificación de que el mensaje de error emitido contenga la descripción esperada
    assert "No se pudo detectar el adaptador OBD-II" in blocker.args[0]
    # Detención del hilo
    trabajador.detener()


# Prueba para validar la transformación de tramas crudas DTC a objetos DTO
def test_controlador_reporte_procesar_dtcs_raw() -> None:
    """Evalúa la conversión de códigos crudos a objetos `DTCDTO` enriquecidos."""
    # Instanciación del controlador de reportes
    controlador = ControladorReporte()
    # Lista de prueba con códigos catalogados y uno no catalogado
    dtcs_raw = ["P0300", "P0113", "P9999"]

    # Procesamiento de la lista cruda
    dtos = controlador.procesar_dtcs_raw(dtcs_raw)

    # Verificación de la cantidad de DTOs generados
    assert len(dtos) == 3
    # Verificación de instancia válida de DTCDTO
    assert isinstance(dtos[0], DTCDTO)

    # Verificación del primer código catalogado (P0300)
    assert dtos[0].codigo == "P0300"
    assert dtos[0].categoria == "Encendido"
    assert dtos[0].gravedad == "Alta"

    # Verificación de la plantilla por defecto para el código no catalogado (P9999)
    assert dtos[2].codigo == "P9999"
    assert dtos[2].categoria == "General"
    assert "no catalogado" in dtos[2].descripcion.lower()


# Prueba para verificar la acumulación de reportes en el historial de sesión
def test_controlador_reporte_generar_reporte_e_historial() -> None:
    """Verifica la generación de reportes formateados y su registro secuencial en memoria."""
    # Instanciación del controlador
    controlador = ControladorReporte()

    # Generación de reporte con falla activa
    reporte1 = controlador.generar_reporte(["P0300"])
    # Generación de reporte sin fallas
    reporte2 = controlador.generar_reporte([])

    # Consulta del historial acumulado
    historial = controlador.obtener_historial()

    # Verificación de estados devueltos
    assert reporte1["estado"] == "Crítico"
    assert reporte2["estado"] == "Sin Fallas"
    # Verificación de que se registraran exactamente 2 reportes en el historial
    assert len(historial) == 2
