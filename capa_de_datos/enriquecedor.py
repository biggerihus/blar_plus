"""
Modulo Orquestador de Datos: EnriquecedorDTC
"""

from typing import Optional
from capa_de_datos.gestor_bd import GestorBD
from capa_de_datos.cliente_rest import ClienteREST
from capa_de_datos.modelo_reporte import DTCReporte

class EnriquecedorDTC:
    def __init__(self, db_path: str = "capa_de_datos/dtc_database.db"):
        self.gestor_bd = GestorBD(db_path)
        self.cliente_rest = ClienteREST()

    def _determinar_gravedad(self, codigo: str) -> str:
        

        codigo_norm = codigo.upper().strip()
        if codigo_norm.startswith("P03"):
            return "Alta"
        elif codigo_norm.startswith("P01"):
            return "Media"
        elif codigo_norm.startswith("B") or codigo_norm.startswith("C"):
            return "Baja"
        return "Media"
    
    def construir_reporte(self, codigo: str) -> DTCReporte:
        codigo_norm = codigo.upper().strip()
        info_local = self.gestor_bd.consultar_codigo(codigo_norm)
        esquema_url = self.cliente_rest.obtener_diagrama_remoto(codigo_norm)

        if info_local:
            description = info_local.get("descripcion", "Sin descripción registrada")
            categoria = info_local.get("categoria", "Desconocido")
        else:
            description = "Código no encontrado en base de datos local"
            categoria = "Genérico"
        
        gravedad = self._determinar_gravedad(codigo_norm)
        solucion_sugerida = f"Inspeccionar componentes relacioandos al código {codigo_norm}"


        return DTCReporte(
            codigo=codigo_norm,
            description=description,
            categoria=categoria,
            gravedad=gravedad,
            solucion_sugerida=solucion_sugerida,
            esquema_url=esquema_url
        ) 