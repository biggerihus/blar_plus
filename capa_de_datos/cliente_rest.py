"""
Modulo ClienteRest
"""

from typing import Optional
import requests

class ClienteREST:
    def __init__(self, url_base: str = "https://api.auto.com/diagrams"):
        self.url_base = url_base.rstrip("/")

    def obtener_diagrama_remoto(self, codigo: str) -> Optional[str]:
        endpoint = f"{self.url_base}/{codigo.lower()}.png"
        try:
            respuesta = requests.get(endpoint, timeout=2.0)
            if respuesta.status_code==200:
                return endpoint
            return None
        except requests.RequestException as err:
            print(f"Aviso de red en clienteREST: {err}")
            return None