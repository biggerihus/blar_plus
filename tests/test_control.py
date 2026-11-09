"""
Suite de Pruebas Unitarias Integradas para la Capa de Control y Concurrencia.

Evalúa:
1. El bucle continuo a 10 Hz y detención segura de `TrabajadorOBD`.
2. La captura de errores de conexión inicial en `TrabajadorOBD`.
3. La transformación de cadenas crudas a objetos `DTCDTO` en `ControladorReporte`.
4. La acumulación de reportes en el historial de sesión.

Autor: Erick Polanco Romero
Capa: Pruebas Unitarias - Núcleo y Controladores / Capa 2
"""

# Importacion de MagicMock para simular comportamientos de objetos de hardware sin dependencias reales
from unittest.mock import MagicMock
# Importacion del marco de pruebas pytest
import pytest
# Importacion de QtBot para interactuar con señales y eventos asíncronos de PySide6
from pytestqt.qtbot import QtBot

# Importacion de la interfaz abstracta IAdaptadorOBD
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
# Importacion de la clase TrabajadorOBD para el manejo del hilo secundario
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
# Importacion del controlador de reportes y la dataclass DTCDTO
from nucleo_y_controladores.controlador_reporte import ControladorReporte, DTCDTO


# Prueba para evaluar el sondeo continuo a 10 Hz y la detencion limpia del hilo secundario
def test_trabajador_obd_sondeo_continuo_y_detencion(qtbot: QtBot) -> None:
    """
    Verifica que `TrabajadorOBD` emita señales en su bucle continuo a 10 Hz
    y finalice adecuadamente al llamar al método `detener()`.

    Pasos:
    1. Simula un adaptador que retorna True en `conectar()` y una lista DTC en `leer_dtc()`.
    2. Espera asíncronamente la emisión de `datos_recibidos` mediante `qtbot.waitSignal`.
    3. Llama a `detener()` y confirma que el hilo deja de ejecutarse (`isRunning() == False`).
    """
    # Creacion de la instancia simulada (mock) basada en la interfaz IAdaptadorOBD
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    # Configuracion del metodo conectar para responder siempre True
    mock_adaptador.conectar.return_value = True
    # Configuracion del metodo leer_dtc para devolver una lista ficticia con dos codigos
    mock_adaptador.leer_dtc.return_value = ["P0300", "P0171"]

    # Instanciacion de la clase TrabajadorOBD inyectando el adaptador simulado
    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # Captura asincrona de la señal datos_recibidos con un tiempo limite de 1000 ms
    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=1000) as blocker:
        # Inicio del hilo secundario de ejecucion
        trabajador.start()

    # Validacion de que los datos emitidos a traves de la señal coincidan con la lista esperada
    assert blocker.args == [["P0300", "P0171"]]

    # Invocacion del metodo detener para finalizar la ejecucion del hilo de forma segura
    trabajador.detener()
    # Aseveracion de que el hilo ha detenido su ejecucion correctamente
    assert not trabajador.isRunning()


# Prueba para verificar la respuesta inmediata cuando falla la conexion del adaptador
def test_trabajador_obd_falla_conexion_inicial(qtbot: QtBot) -> None:
    """
    Verifica la emisión inmediata de `error_ocurrido` si el adaptador no logra conectarse.

    Pasos:
    1. Configura el mock del adaptador para retornar `False` en `conectar()`.
    2. Intercepta la señal de error.
    3. Confirma el mensaje descriptivo y la posterior detención limpia.
    """
    # Creacion de la instancia mock del adaptador
    mock_adaptador = MagicMock(spec=IAdaptadorOBD)
    # Configuracion del metodo conectar para simular un fallo devolviendo False
    mock_adaptador.conectar.return_value = False

    # Instanciacion de TrabajadorOBD con el adaptador defectuoso
    trabajador = TrabajadorOBD(adaptador=mock_adaptador)

    # Intercepcion de la emision de la señal error_ocurrido
    with qtbot.waitSignal(trabajador.error_ocurrido, timeout=1000) as blocker:
        # Arrancado del hilo de ejecucion
        trabajador.start()

    # Verificacion de que el mensaje de error emitido contenga el texto descriptivo esperado
    assert "No se pudo establecer conexión" in blocker.args[0]
    # Detencion del hilo tras el error
    trabajador.detener()


# Prueba para validar la transformacion de listas de texto en objetos DTO
def test_controlador_reporte_procesar_dtcs_raw() -> None:
    """
    Evalúa la transformación de una lista de cadenas crudas DTC a Objetos `DTCDTO`.

    Pasos:
    1. Envía códigos catalogados ("P0300", "P0113") y un código no catalogado ("P9999").
    2. Verifica que se retornen instancias válidas de `DTCDTO`.
    3. Revisa la asignación de campos para el catálogo y para el fallback no catalogado.
    """
    # Instanciacion del controlador de reportes
    controlador = ControladorReporte()
    # Lista de prueba con codigos reconocidos y uno no registrado
    dtcs_raw = ["P0300", "P0113", "P9999"]

    # Procesamiento de la lista cruda a objetos DTCDTO
    dtos = controlador.procesar_dtcs_raw(dtcs_raw)

    # Verificacion de que la lista resultante contenga 3 elementos
    assert len(dtos) == 3
    # Comprobacion de que el primer elemento sea una instancia valida de DTCDTO
    assert isinstance(dtos[0], DTCDTO)

    # Evaluacion de coincidencia en campos del primer codigo catalogado (P0300)
    assert dtos[0].codigo == "P0300"
    # Verificacion de la categoria asignada
    assert dtos[0].categoria == "Encendido"
    # Verificacion del nivel de gravedad asignado
    assert dtos[0].gravedad == "Alta"

    # Evaluacion de la plantilla por defecto (fallback) para el codigo no catalogado (P9999)
    assert dtos[2].codigo == "P9999"
    # Verificacion de la categoria por defecto
    assert dtos[2].categoria == "General"
    # Verificacion de la presencia de la explicacion en la descripcion
    assert "no catalogado" in dtos[2].descripcion


# Prueba para verificar la generacion de reportes y su historial en memoria
def test_controlador_reporte_generar_reporte_e_historial() -> None:
    """Verifica la generación de reportes y la acumulación secuencial en memoria."""
    # Instanciacion del controlador de reportes
    controlador = ControladorReporte()

    # Generacion de un primer reporte con un codigo activo
    reporte1 = controlador.generar_reporte(["P0300"])
    # Generacion de un segundo reporte con lista vacia
    reporte2 = controlador.generar_reporte([])

    # Consulta de la lista de historial acumulado
    historial = controlador.obtener_historial()

    # Verificacion de que el estado con fallas sea Critico
    assert reporte1["estado"] == "Crítico"
    # Verificacion de que el estado sin fallas sea Sin Fallas
    assert reporte2["estado"] == "Sin Fallas"
    # Verificacion de que existan exactamente 2 reportes almacenados en el historial
    assert len(historial) == 2
