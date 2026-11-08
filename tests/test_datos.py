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


from unittest.mock import patch
from capa_de_datos.enriquecedor import EnriquecedorDTC

@patch("capa_de_datos.cliente_rest.ClienteREST.obtener_diagrama_remoto")
def test_enriquecedor_consttruccion_dto(mock_rest):

    """VERIFICA QUE EL ENRIQUECDOR ARME EL DTCReporte 
    CON DATOS LOCALES Y DIAGRAMA SIMULADO"""
    mock_rest.return_value = "https://api.auto.com/diagrams/p0300.png"
    Enriquecedor = EnriquecedorDTC("capa_de_datos/dtc_database.db")

    reporte = Enriquecedor.construir_reporte("P0300")

    assert reporte.codigo == "P0300"
    assert reporte.gravedad == "Alta"
    assert reporte.esquema_url is not None

