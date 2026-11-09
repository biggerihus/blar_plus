"""
Suite de Pruebas de Integración End-to-End para el Sistema Blar Plus.

Evalúa la integración horizontal y el flujo completo de datos entre capas:
Abstracción de Hardware -> Núcleo y Concurrencia -> Interfaz Gráfica (GUI)

Autor: Erick Polanco Romero
Capa: Pruebas de Integración / Control y GUI
"""

# Importación del marco de pruebas pytest
import pytest
# Importación de QtBot para la interceptación de señales y manipulación visual
from pytestqt.qtbot import QtBot

# Importación de componentes de las tres capas
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
from interfaz_grafica.ventana_principal import VentanaPrincipal


# Prueba de integración End-to-End entre el adaptador, el hilo asíncrono y la ventana gráfica
def test_flujo_completo_simulador_gui(qtbot: QtBot) -> None:
    """
    Verifica que las lecturas emitidas por el simulador atraviesen el hilo asíncrono
    y actualicen automáticamente la tabla de diagnósticos en la interfaz gráfica.
    """
    # Instanciación del adaptador simulador
    adaptador = AdaptadorSimulador()
    # Desactivar secuencia de fallos para permitir conexión directa en el test de integración
    adaptador.modo_secuencia_fallos = False

    # Instanciación de la ventana principal de la GUI y registro en qtbot
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    # Instanciación del hilo secundario de control
    trabajador = TrabajadorOBD(adaptador=adaptador)
    ventana.set_trabajador_obd(trabajador)

    # Establecer explícitamente el estado de conexión de la interfaz en True para procesar eventos
    ventana.estadoConexion = True

    # Conectar señal de datos crudos al slot receptor de la ventana
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)

    # Espera asíncrona de la emisión de datos a través de la señal Qt
    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=3000):
        # Iniciar la sesión de sondeo y el hilo de ejecución en segundo plano
        trabajador.iniciar_sondeo()
        trabajador.start()

    # Verificación de que la tabla de diagnósticos en la GUI contenga filas renderizadas (> 0)
    assert ventana.lista_dtc_widget.tabla.rowCount() > 0

    # Invocación de la detención limpia del hilo secundario
    trabajador.detener()
    # Espera sincrónica de QtBot para asegurar la liberación completa del QThread antes de destruir los widgets
    qtbot.waitUntil(lambda: not trabajador.isRunning(), timeout=2000)
    # Aserción final de confirmación de detención del hilo
    assert not trabajador.isRunning()
