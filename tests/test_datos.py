"""
Pruebas Unitarias -Capa de datos SCRUM12
Verifica la conexion y cosnulta a la base de datos SQLite local

Autor: Chavarria Mendoza Antonio
Capa: Pruebas Unitarias - Capa de Datos / Capa 3
"""

# Importacion de pytest para la suite de pruebas unitarias
import pytest 
# Importacion de GestorBD para la consulta de la base de datos local
from capa_de_datos.gestor_bd import GestorBD

# Prueba para comprobar la lectura de un codigo DTC existente en la BD local
def test_consulta_bd_local_existente():
    # Instanciacion del gestor indicando la ruta del archivo SQLite
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    # Consulta del codigo P0300 en la base de datos
    res = gestor.consultar_codigo("P0300")

    # Verificacion de que el resultado devuelto no sea nulo
    assert res is not None, "El codigo P0300 deberia existir en la base de datos"
    # Verificacion de que el campo codigo contenga P0300
    assert "P0300" in res["codigo"]
    # Verificacion de que la clave descripcion este presente en el diccionario
    assert "descripcion" in res
    # Verificacion de que la clave categoria este presente en el diccionario
    assert "categoria" in res

# Prueba para comprobar el comportamiento cuando el codigo no existe en la BD
def test_consulta_bd_codigo_inexistente():
    """Valida el retorno None cuando un código no existe en la base."""
    # Instanciacion del gestor de base de datos
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    # Consulta de un codigo inexistente P9999
    res = gestor.consultar_codigo("P9999")
    # Verificacion de que la respuesta sea None
    assert res is None


# Importacion del decorador patch de unittest.mock para simular llamadas web
from unittest.mock import patch
# Importacion del enriquecedor de datos DTC
from capa_de_datos.enriquecedor import EnriquecedorDTC

# Prueba con mock de la API REST externa para evaluar la construccion del objeto DTCReporte
@patch("capa_de_datos.cliente_rest.ClienteREST.obtener_diagrama_remoto")
def test_enriquecedor_consttruccion_dto(mock_rest):

    """VERIFICA QUE EL ENRIQUECDOR ARME EL DTCReporte 
    CON DATOS LOCALES Y DIAGRAMA SIMULADO"""
    # Establecimiento de la URL retornado simulada por la llamada REST
    mock_rest.return_value = "https://api.auto.com/diagrams/p0300.png"
    # Instanciacion del enriquecedor especificando la ruta de la BD
    Enriquecedor = EnriquecedorDTC("capa_de_datos/dtc_database.db")

    # Construccion del objeto DTO para el codigo P0300
    reporte = Enriquecedor.construir_reporte("P0300")

    # Verificacion de que el codigo asignado sea P0300
    assert reporte.codigo == "P0300"
    # Verificacion de que el nivel de gravedad sea Alta
    assert reporte.gravedad == "Alta"
    # Verificacion de que la URL del esquema haya sido inyectada correctamente
    assert reporte.esquema_url is not None
