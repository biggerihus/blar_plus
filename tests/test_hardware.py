"""
Suite de Pruebas Unitarias para la Capa de Abstracción de Hardware (HAL).

Autor: Mendivil Jimenez Jose Luis & Estrada Loaiza Rogelio
Capa: Pruebas Unitarias - Abstracción de Hardware / Capa 4
"""

# Importación del marco de pruebas pytest
import pytest
# Importación del adaptador simulador de la Capa HAL
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador


# Prueba para verificar la conexión inicial y la lectura de códigos DTC
def test_simulador_conexion_y_lectura() -> None:
    """Verifica que el simulador se conecte, devuelva una lista de DTCs y se desconecte limpiamente."""
    # Instanciación del objeto simulador
    sim = AdaptadorSimulador()
    # Desactivar secuencia de fallos para probar la conexión estándar
    sim.modo_secuencia_fallos = False

    # Comprobación de que la conexión retorne True
    assert sim.conectar("/dev/ttyUSB0") is True
    # Comprobación de que el estado de conexión interno sea True
    assert sim.conectado is True

    # Lectura de la lista de códigos DTC activos
    dtcs = sim.leer_dtc()
    # Verificación de que el resultado sea una estructura de lista
    assert isinstance(dtcs, list)
    # Verificación de que la lista contenga al menos un código simulado
    assert len(dtcs) > 0

    # Ejecución de la desconexión del adaptador
    sim.desconectar()
    # Comprobación de que el adaptador haya actualizado su estado a False
    assert sim.conectado is False


# Prueba para validar la protección de lectura sin conexión
def test_simulador_lectura_sin_conexion() -> None:
    """Comprueba que el simulador genere RuntimeError si se leen DTCs estando desconectado."""
    # Instanciación del simulador sin invocar conectar()
    sim = AdaptadorSimulador()

    # Verificación de captura de excepción RuntimeError
    with pytest.raises(RuntimeError):
        sim.leer_dtc()


# Prueba para validar la correlación física y rangos válidos de PIDs
def test_simulador_lectura_pid() -> None:
    """Comprueba que las lecturas de PIDs generen valores en coma flotante dentro de rangos físicos válidos."""
    # Instanciación del simulador
    sim = AdaptadorSimulador()
    # Desactivar secuencia de fallos
    sim.modo_secuencia_fallos = False
    # Conexión al adaptador
    sim.conectar("/dev/ttyUSB0")

    # Lectura de RPM (PID 010C)
    rpm = sim.leer_pid("010C")
    # Lectura de Velocidad (PID 010D)
    velocidad = sim.leer_pid("010D")

    # Verificación de tipo float para RPM
    assert isinstance(rpm, float)
    # Verificación de rango físico permitido de RPM (750.0 RPM a 3500.0 RPM considerando fluctuación en ralentí)
    assert 750.0 <= rpm <= 3500.0

    # Verificación de tipo float para velocidad
    assert isinstance(velocidad, float)
    # Verificación de rango físico permitido de velocidad (0.0 km/h a 120.0 km/h)
    assert 0.0 <= velocidad <= 120.0

    # Desconexión limpia
    sim.desconectar()


# Prueba para validar el borrado de códigos DTC simulados
def test_simulador_limpiar_dtc() -> None:
    """Comprueba que la orden de borrado limpie la memoria de códigos en la ECU simulada."""
    # Instanciación del simulador
    sim = AdaptadorSimulador()
    # Desactivar secuencia de fallos
    sim.modo_secuencia_fallos = False
    # Conexión al adaptador
    sim.conectar("/dev/ttyUSB0")

    # Ejecución de la operación de borrado total
    resultado = sim.limpiar_dtc()
    # Verificación de respuesta exitosa
    assert resultado is True
    # Verificación de que la lista de DTCs remanentes esté vacía
    assert sim.leer_dtc() == []

    # Desconexión limpia
    sim.desconectar()


# Prueba para comprobar el rechazo de PIDs no soportados
def test_simulador_pid_no_soportado() -> None:
    """Comprueba que la consulta de un PID no catalogado provoque un ValueError."""
    # Instanciación del simulador
    sim = AdaptadorSimulador()
    sim.modo_secuencia_fallos = False
    sim.conectar("/dev/ttyUSB0")

    # Verificación de lanzamiento de ValueError ante un PID inválido
    with pytest.raises(ValueError):
        sim.leer_pid("9999")

    # Desconexión limpia
    sim.desconectar()


# Prueba para validar la máquina de secuencia de fallos físicos
def test_simulador_secuencia_fallos() -> None:
    """Valida la secuencia de fallos: Rechazo en 1.er intento y conexión exitosa en 2.º intento."""
    # Instanciación del simulador
    sim = AdaptadorSimulador()
    # Activar explícitamente el modo de secuencia de fallos
    sim.modo_secuencia_fallos = True
    sim.intentos_conexion = 0

    # 1.er Intento: Debe ser rechazado (conectar() -> False)
    assert sim.conectar() is False
    assert sim.conectado is False

    # 2.º Intento: Debe ser aceptado (conectar() -> True)
    assert sim.conectar() is True
    assert sim.conectado is True

    # Desconexión al finalizar la prueba
    sim.desconectar()
