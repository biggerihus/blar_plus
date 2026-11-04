"""
DTCReporte
Codigo de falla
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DTCReporte:
    codigo: str
    description: str
    categoria: str
    gravedad: str
    solucion_sugerida: str
    esquema_url: Optional[str] = None