"""
Suite de Pruebas de Integración End-to-End para el Sistema Blar Plus.

Evalúa la integración horizontal y el flujo completo de datos entre capas
utilizando el Modo Simulador autónomo y el borrado asíncrono exclusivo en hilo OBD:
Abstracción de Hardware -> Núcleo y Concurrencia -> Interfaz Gráfica (GUI)

Autor: Erick Polanco Romero
Capa: Pruebas de Integración / Control y GUI
"""

# Importación de patch para interceptar diálogos modales QMessageBox y QDialog sin bloquear pytest
from unittest.mock import patch
# Importación del marco de pruebas pytest
import pytest
# Importación de QDialog y QMessageBox para validar ventanas emergentes
from PySide6.QtWidgets import QDialog, QMessageBox
# Importación de QtBot para la interceptación de señales y manipulación visual
from pytestqt.qtbot import QtBot

# Importación de componentes de las tres capas
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
from interfaz_grafica.ventana_principal import VentanaPrincipal


# Prueba 1: Flujo End-to-End estándar entre simulador (5 DTCs), hilo asíncrono y tabla GUI
def test_flujo_completo_simulador_gui(qtbot: QtBot) -> None:
    """
    Verifica que los 5 códigos DTC y sensores emitidos por el simulador atraviesen
    el hilo asíncrono y actualicen automáticamente la tabla en la interfaz gráfica.
    """
    adaptador = AdaptadorSimulador()
    adaptador.modo_secuencia_fallos = False

    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    trabajador = TrabajadorOBD(adaptador=adaptador)
    ventana.set_trabajador_obd(trabajador)
    ventana.estadoConexion = True

    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)

    try:
        trabajador.iniciar_sondeo()
        trabajador.start()

        qtbot.waitUntil(lambda: ventana.lista_dtc_widget.tabla.rowCount() == 5, timeout=3000)
        assert ventana.lista_dtc_widget.tabla.rowCount() == 5
    finally:
        trabajador.detener()
        qtbot.waitUntil(lambda: not trabajador.isRunning(), timeout=2000)
        assert not trabajador.isRunning()


# Prueba 2: Secuencia autónoma de fallo inicial en Modo Simulador y reconexión en 2.º intento
def test_simulador_secuencia_fallo_inicial_y_reconexion_gui(qtbot: QtBot) -> None:
    """
    Valida el ciclo autónomo del Modo Simulador sin controles extra en la GUI:
    1. Primer clic en Conectar dispara ventana crítica de error (QMessageBox.critical).
    2. Segundo clic en Conectar establece enlace y carga los 5 códigos del semáforo.
    """
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    idx_simulador = ventana.combo_puerto_modo.findData("SIMULADOR")
    assert idx_simulador >= 0
    ventana.combo_puerto_modo.setCurrentIndex(idx_simulador)

    simulador = AdaptadorSimulador()
    simulador.modo_secuencia_fallos = True
    ventana._adaptador_simulador = simulador

    trabajador = TrabajadorOBD(adaptador=simulador)
    ventana.set_trabajador_obd(trabajador)
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)
    trabajador.sensores_recibidos.connect(ventana.recibir_sensores_asincronos)
    trabajador.start()

    try:
        # 1.er Intento: Debe fallar y lanzar QMessageBox.critical
        with patch.object(QMessageBox, "critical") as mock_critical:
            ventana.alternar_conexion()
            assert ventana.estadoConexion is False
            mock_critical.assert_called_once()
            assert "Error de Comunicación OBD-II" in mock_critical.call_args[0][1]

        # 2.º Intento: Debe conectar correctamente y renderizar los 5 DTCs representativos
        ventana.alternar_conexion()
        qtbot.waitUntil(lambda: len(ventana.reportes_actuales) == 5, timeout=3000)

        assert ventana.estadoConexion is True
        assert "Toyota Corolla" in ventana.lbl_banner_vehiculo.text()
        codigos_renderizados = [dto.codigo for dto in ventana.reportes_actuales]
        assert codigos_renderizados == ["P0300", "P0171", "P0420", "P0442", "U0100"]
    finally:
        trabajador.detener()
        qtbot.waitUntil(lambda: not trabajador.isRunning(), timeout=2000)


# Prueba 3: Desconexión física en caliente durante sesión activa del Modo Simulador
def test_simulador_desconexion_fisica_en_caliente_y_alerta_critica(qtbot: QtBot) -> None:
    """
    Valida que al cumplirse el límite de sesión en el 2.º intento del simulador,
    se dispare QMessageBox.critical, se reinicie la interfaz y se limpien los DTCs.
    """
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    idx_simulador = ventana.combo_puerto_modo.findData("SIMULADOR")
    ventana.combo_puerto_modo.setCurrentIndex(idx_simulador)

    simulador = AdaptadorSimulador()
    simulador.modo_secuencia_fallos = True
    simulador.intentos_conexion = 1
    simulador.tiempo_limite_sesion = 0.25
    ventana._adaptador_simulador = simulador

    trabajador = TrabajadorOBD(adaptador=simulador)
    ventana.set_trabajador_obd(trabajador)
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)
    trabajador.start()

    try:
        with patch.object(QMessageBox, "critical") as mock_critical:
            ventana.alternar_conexion()
            assert ventana.estadoConexion is True

            qtbot.waitUntil(lambda: ventana.estadoConexion is False, timeout=3000)

            mock_critical.assert_called_once()
            assert "desconectado físicamente" in mock_critical.call_args[0][2]
            assert ventana.lista_dtc_widget.tabla.rowCount() == 0
            assert ventana.combo_puerto_modo.isEnabled() is True
    finally:
        trabajador.detener()
        qtbot.waitUntil(lambda: not trabajador.isRunning(), timeout=2000)


# Prueba 4: Borrado asíncrono exclusivo de códigos DTC y simulación de rechazo por la ECU
def test_simulador_borrado_dtc_rechazo_cancelar_y_confirmar(qtbot: QtBot) -> None:
    """
    Verifica el flujo asíncrono de seguridad al presionar el botón de borrado:
    - Si la ECU simulada rechaza el borrado en el hilo secundario, emite rechazo,
      lanza QMessageBox.warning en la GUI y conserva los 5 DTCs.
    - Al cancelar el diálogo modal, los 5 códigos permanecen intactos.
    - Al confirmar en modo normal, el hilo OBD borra los códigos y la GUI se vacía.
    """
    ventana = VentanaPrincipal()
    qtbot.addWidget(ventana)

    idx_simulador = ventana.combo_puerto_modo.findData("SIMULADOR")
    ventana.combo_puerto_modo.setCurrentIndex(idx_simulador)

    simulador = AdaptadorSimulador()
    simulador.modo_secuencia_fallos = False
    simulador.simular_rechazo_borrado = True
    ventana._adaptador_simulador = simulador

    trabajador = TrabajadorOBD(adaptador=simulador)
    ventana.set_trabajador_obd(trabajador)
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)
    trabajador.start()

    try:
        ventana.alternar_conexion()
        qtbot.waitUntil(lambda: len(ventana.reportes_actuales) == 5, timeout=3000)

        # Caso A: ECU rechaza el borrado -> Lanza QMessageBox.warning y conserva los 5 códigos
        with patch.object(DialogoConfirmacion, "exec", return_value=QDialog.DialogCode.Accepted):
            with patch.object(QMessageBox, "warning") as mock_warning:
                ventana.abrir_dialogo_borrado()
                qtbot.waitUntil(lambda: mock_warning.called, timeout=3000)
                mock_warning.assert_called_once()
                assert "Borrado Rechazado por la ECU" in mock_warning.call_args[0][1]
                assert len(ventana.reportes_actuales) == 5

        # Habilitar aceptación normal de borrado en la ECU simulada
        simulador.simular_rechazo_borrado = False

        # Caso B: Usuario cancela en DialogoConfirmacion -> No se borra nada
        with patch.object(DialogoConfirmacion, "exec", return_value=QDialog.DialogCode.Rejected):
            ventana.abrir_dialogo_borrado()
            assert len(ventana.reportes_actuales) == 5
            assert len(simulador.leer_dtc()) == 5

        # Caso C: Usuario confirma en DialogoConfirmacion -> Hilo OBD borra simulador y GUI
        with patch.object(DialogoConfirmacion, "exec", return_value=QDialog.DialogCode.Accepted):
            ventana.abrir_dialogo_borrado()
            qtbot.waitUntil(lambda: len(ventana.reportes_actuales) == 0, timeout=3000)
            assert simulador.leer_dtc() == []
            assert ventana.lista_dtc_widget.tabla.rowCount() == 0
    finally:
        trabajador.detener()
        qtbot.waitUntil(lambda: not trabajador.isRunning(), timeout=2000)
