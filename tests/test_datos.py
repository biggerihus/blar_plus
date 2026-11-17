"""
Suite de Pruebas Unitarias para la Capa de Datos.

Evalúa:
1. La auto-inicialización y consulta de códigos DTC en la base de datos SQLite local.
2. El manejo de consultas para códigos no existentes y el almacenamiento en caché.
3. El enriquecimiento de reportes integrando datos locales, decodificación SAE y llamadas REST simuladas.

Autor: Chavarria Mendoza Antonio
Capa: Pruebas Unitarias - Capa de Datos / Capa 3
"""

# Importación de Path para manejo limpio de rutas temporales de prueba
from pathlib import Path
# Importación de pytest para el marco de pruebas
import pytest
# Importación del decorador patch de unittest.mock
from unittest.mock import patch

# Importación del gestor de base de datos SQLite
from capa_de_datos.gestor_bd import GestorBD
# Importación del enriquecedor de datos DTC
from capa_de_datos.enriquecedor import EnriquecedorDTC


# Prueba para verificar la lectura de códigos DTC cargados desde el catálogo maestro
def test_consulta_bd_local_existente(tmp_path: Path) -> None:
    """Comprueba la auto-inicialización y lectura técnica de códigos estándar en SQLite."""
    # Ruta de base de datos temporal aislada para la prueba
    db_prueba = str(tmp_path / "test_dtc.db")
    # Instanciación del gestor de base de datos con auto-inicialización
    gestor = GestorBD(db_prueba)

    # Verificación de carga masiva del catálogo maestro (> 100 códigos)
    assert gestor.contar_codigos() >= 100

    # Consulta del código P0300
    res_p0300 = gestor.consultar_codigo("P0300")
    assert res_p0300 is not None, "El código P0300 debería existir en la base de datos local."
    assert res_p0300["codigo"] == "P0300"
    assert "descripcion" in res_p0300
    assert "categoria" in res_p0300
    assert "gravedad" in res_p0300
    assert "solucion" in res_p0300

    # Consulta del código P0171
    res_p0171 = gestor.consultar_codigo("P0171")
    assert res_p0171 is not None
    assert res_p0171["categoria"] == "Combustible"
    assert res_p0171["gravedad"] == "Media"


# Prueba para verificar el comportamiento ante códigos no registrados y caché de escritura
def test_consulta_bd_codigo_inexistente_y_cache(tmp_path: Path) -> None:
    """Valida que un código inexistente devuelva None y pueda persistirse en caché local."""
    # Ruta de base de datos temporal aislada
    db_prueba = str(tmp_path / "test_cache.db")
    gestor = GestorBD(db_prueba)

    # Consulta de código propietario no registrado inicialmente
    assert gestor.consultar_codigo("P1456") is None

    # Persistencia en caché local mediante guardar_codigo
    guardado = gestor.guardar_codigo(
        codigo="P1456",
        descripcion="Fuga detectada en sistema EVAP (tanque de combustible).",
        categoria="Emisiones",
        gravedad="Baja",
        solucion="Revisar tapón de combustible y válvula de control de emisiones evaporativas.",
    )
    assert guardado is True

    # Verificación de recuperación posterior desde SQLite
    recuperado = gestor.consultar_codigo("P1456")
    assert recuperado is not None
    assert recuperado["codigo"] == "P1456"
    assert recuperado["categoria"] == "Emisiones"


# Prueba con Mock de la API REST externa para evaluar la construcción del objeto formateado
@patch("capa_de_datos.cliente_rest.ClienteREST.obtener_diagrama_remoto")
def test_enriquecedor_construccion_dto(mock_rest, tmp_path: Path) -> None:
    """Verifica que el enriquecedor arme el reporte combinando SQLite, respaldo SAE y URL remota."""
    # Ruta de base de datos temporal aislada
    db_prueba = str(tmp_path / "test_enriquecedor.db")
    # Simulación de la URL devuelta por la API REST externa
    mock_rest.return_value = "https://api.auto.com/diagrams/p0300.png"
    # Instanciación del enriquecedor de datos DTC
    enriquecedor = EnriquecedorDTC(db_prueba)

    # 1. Construcción de reporte para código existente en SQLite (P0300)
    reporte_local = enriquecedor.construir_reporte("P0300")
    assert reporte_local.codigo == "P0300"
    assert reporte_local.gravedad == "Alta"
    assert reporte_local.esquema_url == "https://api.auto.com/diagrams/p0300.png"

    # 2. Construcción de reporte para código específico de fabricante fuera de SQLite (P1320)
    reporte_oem = enriquecedor.construir_reporte("P1320")
    assert reporte_oem.codigo == "P1320"
    assert reporte_oem.categoria == "Encendido"
    assert reporte_oem.gravedad == "Alta"
    assert "fabricante (OEM)" in reporte_oem.description
