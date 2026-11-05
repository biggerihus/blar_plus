"""
Pruebas Unitarias -Capa de datos SCRUM12
Verifica la conexion y cosnulta a la base de datos SQLite local
"""

import pytest 
from capa_de_datos.gestor_bd import GestorBD

def test_consulta_bd_local_existente():
    
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    res = gestor.consultar_codigo("P0300")

    assert res is not None, "El codigo P0300 deberia existir en la base de datos"
    assert "P0300"  in res["codigo"]
    assert "descripcion" in res
    assert "categoria" in res

def test_consulta_bd_codigo_inexistente():
    """Valida el retorno None cuando un código no existe en la base."""
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    res = gestor.consultar_codigo("P9999")
    assert res is None
