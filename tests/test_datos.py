"""
Suite de Pruebas Unitarias para la Capa de Datos.

Evalúa:
1. La consulta de códigos DTC en la base de datos SQLite local.
2. El manejo de consultas para códigos no existentes.
3. El enriquecimiento de reportes integrando datos locales y llamadas REST simuladas.

Autor: Chavarria Mendoza Antonio
Capa: Pruebas Unitarias - Capa de Datos / Capa 3
"""

# Importación de pytest para el marco de pruebas
import pytest
# Importación del decorador patch de unittest.mock
from unittest.mock import patch

# Importación del gestor de base de datos SQLite
from capa_de_datos.gestor_bd import GestorBD
# Importación del enriquecedor de datos DTC
from capa_de_datos.enriquecedor import EnriquecedorDTC


# Prueba para verificar la lectura de un código DTC presente en la BD local
def test_consulta_bd_local_existente() -> None:
    """Comprueba la lectura correcta de información técnica para el código P0300."""
    # Instanciación del gestor de base de datos
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    # Consulta del código P0300
    res = gestor.consultar_codigo("P0300")

    # Verificación de que el resultado no sea nulo
    assert res is not None, "El código P0300 debería existir en la base de datos local."
    # Verificación de concordancia en el campo de código
    assert "P0300" in res["codigo"]
    # Verificación de presencia de claves descriptivas esenciales
    assert "descripcion" in res
    assert "categoria" in res


# Prueba para verificar el comportamiento ante códigos no registrados en la BD local
def test_consulta_bd_codigo_inexistente() -> None:
    """Valida que la consulta de un código inexistente devuelva None."""
    # Instanciación del gestor de BD
    gestor = GestorBD("capa_de_datos/dtc_database.db")
    # Consulta de código no registrado
    res = gestor.consultar_codigo("P9999")
    # Verificación de retorno Nulo
    assert res is None


# Prueba con Mock de la API REST externa para evaluar la construcción del objeto formateado
@patch("capa_de_datos.cliente_rest.ClienteREST.obtener_diagrama_remoto")
def test_enriquecedor_construccion_dto(mock_rest) -> None:
    """Verifica que el enriquecedor arme el objeto de reporte combinando datos locales y remotos."""
    # Simulación de la URL devuelta por la API REST externa
    mock_rest.return_value = "https://api.auto.com/diagrams/p0300.png"
    # Instanciación del enriquecedor de datos DTC
    enriquecedor = EnriquecedorDTC("capa_de_datos/dtc_database.db")

    # Construcción del reporte para el código P0300
    reporte = enriquecedor.construir_reporte("P0300")

    # Verificación de que el código asignado sea P0300
    assert reporte.codigo == "P0300"
    # Verificación del nivel de gravedad
    assert reporte.gravedad == "Alta"
    # Verificación de la inyección de la URL remota simulada
    assert reporte.esquema_url is not None
