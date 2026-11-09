"""
DTCReporte
Codigo de falla
Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importacion del decorador dataclass para la creacion automatica de clases de datos
from dataclasses import dataclass
# Importacion de Optional para tipado de atributos que pueden ser nulos
from typing import Optional

# Entidad DTO que estructura el reporte consolidado de un codigo DTC
@dataclass
class DTCReporte:
    # Codigo alfanumerico estandar del DTC (ejemplo: 'P0300')
    codigo: str
    # Descripcion explicativa de la falla o diagnostico
    description: str
    # Categoria del sistema afectado (Powertrain, Body, Chassis, Network)
    categoria: str
    # Nivel de severidad o prioridad (Alta, Media, Baja)
    gravedad: str
    # Recomendacion o paso a seguir para la solucion de la falla
    solucion_sugerida: str
    # Enlace a la imagen o diagrama electrico remoto si esta disponible
    esquema_url: Optional[str] = None
