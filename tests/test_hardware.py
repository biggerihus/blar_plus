# Estas pruebas sirven para comprobar que el simulador funciona correctamente.
# Por ejemplo: conectarse, leer fallas, leer sensores y borrar códigos.

import pytest
# Importamos pytest, una herramienta para realizar pruebas en Python. Nos ayuda a verificar si las funciones trabajan correctamente.

from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
# AdaptadorSimulador esta clase imita el funcionamiento de un adaptador OBD-II sin necesidad de conectarnos a un automóvil real.


def test_simulador_conexion_y_lectura():
    # Esta prueba verifica que el simulador pueda conectarse,
    # leer códigos de falla y desconectarse.

    sim = AdaptadorSimulador()
    # Creamos un objeto llamado sim para utilizar el simulador.

    assert sim.conectar("/dev/ttyUSB0") is True
    # Intentamos conectar el simulador.
    # assert comprueba que una condición sea verdadera.
    # Si conectar() devuelve True, la prueba continúa.
    # Si devuelve False, la prueba falla.

    dtcs = sim.leer_dtc()
    # Leemos los códigos de falla simulados.
    # Guardamos los códigos encontrados en la variable dtcs.

    assert isinstance(dtcs, list)
    # Verificamos que dtcs sea una lista.
    # isinstance() comprueba el tipo de dato.
    # Por ejemplo: ["P0300", "P0171"] es una lista.

    assert len(dtcs) > 0
    # len(dtcs) cuenta cuántos elementos tiene la lista.
    # > 0 significa que debe tener al menos un código.
    # Si está vacía, la prueba falla.

    sim.desconectar()
    # Desconectamos el simulador.

    assert sim.conectado is False
    # Comprobamos que el simulador esté desconectado.
    # False significa que ya no existe una conexión activa.


def test_simulador_lectura_sin_conexion():
    """Comprueba que no se puedan leer DTC sin conexión."""

    # Esta prueba verifica que el simulador genere un error
    # si intentamos leer fallas sin conectarnos primero.

    sim = AdaptadorSimulador()
    # Creamos el simulador, pero no lo conectamos.

    with pytest.raises(RuntimeError):
        # pytest.raises() comprueba que ocurra un error esperado.
        # RuntimeError es el tipo de error que esperamos.
        #
        # En este caso, el error es correcto porque
        # estamos intentando leer sin conexión.

        sim.leer_dtc()
        # Intentamos leer códigos de falla.
        # Como no estamos conectados, debe aparecer RuntimeError.
        # Si aparece ese error, la prueba pasa.


def test_simulador_lectura_pid():
    """Comprueba que los sensores generen valores dentro del rango."""

    # Esta prueba verifica que las RPM y la velocidad
    # sean números decimales dentro de los rangos permitidos.

    sim = AdaptadorSimulador()
    # Creamos el simulador.

    sim.conectar("/dev/ttyUSB0")
    # Conectamos el simulador.

    rpm = sim.leer_pid("010C")
    # Consultamos el PID 010C, que corresponde a las RPM.
    # Guardamos el resultado en rpm.
    # Por ejemplo: 1500.0 RPM.

    velocidad = sim.leer_pid("010D")
    # Consultamos el PID 010D, que corresponde a la velocidad.
    # Guardamos el resultado en velocidad.
    # Por ejemplo: 60.0 km/h.

    assert isinstance(rpm, float)
    # Comprobamos que las RPM sean un número decimal (float).
    # Por ejemplo: 1500.0

    assert 800.0 <= rpm <= 3000.0
    # Verificamos que las RPM estén entre 800 y 3000.
    #
    # <= significa "menor o igual que".
    # Por ejemplo:
    # rpm = 1500.0 -> Correcto.
    # rpm = 3500.0 -> La prueba falla.

    assert isinstance(velocidad, float)
    # Comprobamos que la velocidad sea un número decimal.
    # Por ejemplo: 60.0

    assert 0.0 <= velocidad <= 120.0
    # Verificamos que la velocidad esté entre 0 y 120 km/h.
    #
    # Por ejemplo:
    # velocidad = 80.0 -> Correcto.
    # velocidad = 150.0 -> La prueba falla.

    sim.desconectar()
    # Desconectamos el simulador al terminar.


def test_simulador_limpiar_dtc():
    """Comprueba que se puedan borrar los códigos simulados."""

    # Esta prueba verifica que el simulador pueda borrar
    # los códigos de falla almacenados.

    sim = AdaptadorSimulador()
    # Creamos el simulador.

    sim.conectar("/dev/ttyUSB0")
    # Conectamos el simulador.

    resultado = sim.limpiar_dtc()
    # Ejecutamos la función que borra los códigos de falla.
    # Guardamos el resultado en la variable resultado.

    assert resultado is True
    # Comprobamos que la función devuelva True.
    # Esto indica que el simulador reportó el borrado como exitoso.

    assert sim.leer_dtc() == []
    # Volvemos a consultar los códigos de falla.
    # == significa "es igual a".
    # [] representa una lista vacía.
    #
    # Si devuelve [], significa que no quedan códigos.
    # Si todavía hay códigos, la prueba falla.

    sim.desconectar()
    # Desconectamos el simulador.


def test_simulador_pid_no_soportado():
    """Comprueba el manejo de identificadores PID desconocidos."""

    # Esta prueba verifica que el simulador genere un error
    # cuando intentamos consultar un PID que no reconoce.

    sim = AdaptadorSimulador()
    # Creamos el simulador.

    sim.conectar("/dev/ttyUSB0")
    # Conectamos el simulador.

    with pytest.raises(ValueError):
        # Indicamos que esperamos un error de tipo ValueError.
        #
        # ValueError aparece cuando proporcionamos
        # un valor que la función no acepta.
        #
        # Si aparece este error, la prueba pasa.

        sim.leer_pid("9999")
        # Intentamos consultar el PID 9999.
        # Este PID no está soportado por el simulador.
        # Por eso esperamos que genere ValueError.

    sim.desconectar()
    # Desconectamos el simulador.
