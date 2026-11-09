""""
Modulo ClienteRest
Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importacion de Optional para retornos que pueden devolver un valor o None
from typing import Optional
# Importacion de la libreria requests para realizar consultas HTTP síncronas
import requests

# Clase cliente para verificar y consumir recursos graficos en una API web externa
class ClienteREST:
    # Inicializador que configura la URL base del servidor remoto
    def __init__(self, url_base: str = "https://api.auto.com/diagrams"):
        # Limpieza de diagonales al final de la cadena de la URL
        self.url_base = url_base.rstrip("/")

    # Realiza una peticion GET para verificar si existe la imagen del esquema de cableado
    def obtener_diagrama_remoto(self, codigo: str) -> Optional[str]:
        # Construccion del endpoint en minusculas apuntando a la extension PNG
        endpoint = f"{self.url_base}/{codigo.lower()}.png"
        # Bloque try para capturar incidencias en la peticion de red
        try:
            # Ejecucion de la solicitud GET definiendo un tiempo limite de respuesta de 2.0s
            respuesta = requests.get(endpoint, timeout=2.0)
            # Evaluacion del codigo de estado de la respuesta HTTP igual a 200 OK
            if respuesta.status_code == 200:
                # Retorno del enlace completo del diagrama si existe en el servidor
                return endpoint
            # Retorno nulo si el codigo de respuesta es diferente a 200
            return None
        # Captura de excepciones asociadas a fallos de red o tiempos de espera agotados
        except requests.RequestException as err:
            # Reporte informativo en consola sobre el problema de red
            print(f"Aviso de red en clienteREST: {err}")
            # Retorno nulo por fallo en la consulta remota
            return None
