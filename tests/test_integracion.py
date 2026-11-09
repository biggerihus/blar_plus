"""
Suite de Pruebas de Integración End-to-End para el Sistema Blar Plus.

Evalúa la integración horizontal y el flujo completo de datos entre capas:
Abstracción de Hardware -> Núcleo y Concurrencia -> Interfaz Gráfica (GUI)

Autor: Erick Polanco Romero
Capa: Pruebas de Integración / Control y GUI
"""

# Importacion del marco de pruebas pytest
import pytest
# Importacion de QtBot para interceptar señales asíncronas y manipular la interfaz gráfica
from pytestqt.qtbot import QtBot

# Importacion del adaptador simulador de la Capa de Hardware
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
# Importacion del hilo trabajador asíncrono de la Capa de Control
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
# Importacion de la ventana principal de la Capa de Interfaz Gráfica
from interfaz_grafica.ventana_principal import VentanaPrincipal


# Funcion de prueba de integracion end-to-end entre el simulador, el hilo y la GUI
def test_flujo_completo_simulador_gui(qtbot: QtBot) -> None:
    """
    Verifica que las lecturas del simulador atraviesen el hilo asíncrono
    y actualicen automáticamente la tabla de la interfaz gráfica.
    """
    # Instanciacion del adaptador de hardware en modo simulacion
    adaptador = AdaptadorSimulador()
    # Instanciacion de la ventana principal de la interfaz de usuario
    ventana = VentanaPrincipal()
    # Registro del widget principal en el asistente de pruebas QtBot
    qtbot.addWidget(ventana)

    # Instanciacion del hilo secundario de control inyectando el adaptador simulado
    trabajador = TrabajadorOBD(adaptador=adaptador)

    # Establecimiento del enlace de señales Qt entre el hilo secundario y la ventana principal
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)

    # Espera asíncrona de la emision de la señal datos_recibidos con tiempo limite de 3000 ms
    with qtbot.waitSignal(trabajador.datos_recibidos, timeout=3000):
        # Arranque de la ejecucion en segundo plano del hilo trabajador
        trabajador.start()

    # Verificacion de que la tabla de diagnostico en la GUI haya renderizado los registros
    assert ventana.lista_dtc_widget.tabla.rowCount() > 0

    # Invocacion de la detencion limpia del hilo trabajador secundario
    trabajador.detener()
    # Aseveracion de confirmacion de que el hilo ha dejado de ejecutarse
    assert not trabajador.isRunning()
