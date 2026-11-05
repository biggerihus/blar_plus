
"""
Pruebas unitarias del módulo de hardware de Blar Plus.
"""

import pytest

from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador


def test_simulador_conexion_y_lectura():
    sim = AdaptadorSimulador()
    assert sim.conectar("/dev/ttyUSB0") is True
    dtcs = sim.leer_dtc()
    assert isinstance(dtcs, list)
    assert len(dtcs) > 0
    sim.desconectar()
    assert sim.conectado is False


def test_simulador_lectura_sin_conexion():
    """Comprueba que no se puedan leer DTC sin conexión."""

    sim = AdaptadorSimulador()

    with pytest.raises(RuntimeError):
        sim.leer_dtc()


def test_simulador_lectura_pid():
    """Comprueba que los sensores generen valores dentro del rango."""

    sim = AdaptadorSimulador()
    sim.conectar("/dev/ttyUSB0")

    rpm = sim.leer_pid("010C")
    velocidad = sim.leer_pid("010D")

    assert isinstance(rpm, float)
    assert 800.0 <= rpm <= 3000.0

    assert isinstance(velocidad, float)
    assert 0.0 <= velocidad <= 120.0

    sim.desconectar()


def test_simulador_limpiar_dtc():
    """Comprueba que se puedan borrar los códigos simulados."""

    sim = AdaptadorSimulador()
    sim.conectar("/dev/ttyUSB0")

    resultado = sim.limpiar_dtc()

    assert resultado is True
    assert sim.leer_dtc() == []

    sim.desconectar()


def test_simulador_pid_no_soportado():
    """Comprueba el manejo de identificadores PID desconocidos."""

    sim = AdaptadorSimulador()
    sim.conectar("/dev/ttyUSB0")

    with pytest.raises(ValueError):
        sim.leer_pid("9999")

    sim.desconectar()
