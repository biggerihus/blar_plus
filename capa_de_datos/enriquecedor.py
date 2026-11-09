"""
Modulo Orquestador de Datos: EnriquecedorDTC
Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importacion de Optional para anotaciones de tipo
from typing import Optional
# Importacion de la clase GestorBD para consultar datos locales
from capa_de_datos.gestor_bd import GestorBD
# Importacion del ClienteREST para recuperar diagramas remotos
from capa_de_datos.cliente_rest import ClienteREST
# Importacion de la estructura DTO DTCReporte
from capa_de_datos.modelo_reporte import DTCReporte

# Clase principal encargada de combinar informacion local, remota y reglas de negocio
class EnriquecedorDTC:
    # Inicializador que compone e instancia los servicios de BD y cliente REST
    def __init__(self, db_path: str = "capa_de_datos/dtc_database.db"):
        # Instanciacion del gestor de persistencia SQLite
        self.gestor_bd = GestorBD(db_path)
        # Instanciacion del cliente para consulta de servicios web
        self.cliente_rest = ClienteREST()

    # Metodo interno para categorizar la gravedad del fallo segun el prefijo OBD-II
    def _determinar_gravedad(self, codigo: str) -> str:
        # Conversion a mayusculas y limpieza de espacios en blanco
        codigo_norm = codigo.upper().strip()
        # Evaluacion si el codigo pertenece a la serie P03 (fallos en encendido o cilindros)
        if codigo_norm.startswith("P03"):
            # Asignacion de nivel de gravedad Alta
            return "Alta"
        # Evaluacion si el codigo pertenece a la serie P01 (medicion de aire/combustible)
        elif codigo_norm.startswith("P01"):
            # Asignacion de nivel de gravedad Media
            return "Media"
        # Evaluacion si el codigo corresponde a la carroceria (B) o chasis (C)
        elif codigo_norm.startswith("B") or codigo_norm.startswith("C"):
            # Asignacion de nivel de gravedad Baja
            return "Baja"
        # Retorno de gravedad Media como valor por defecto
        return "Media"

    # Construye el objeto DTCReporte integrando la definicion local, la URL remota y la gravedad
    def construir_reporte(self, codigo: str) -> DTCReporte:
        # Normalizacion estandar del codigo alfanumerico
        codigo_norm = codigo.upper().strip()
        # Búsqueda de la definicion local en el archivo SQLite
        info_local = self.gestor_bd.consultar_codigo(codigo_norm)
        # Consulta remota de disponibilidad del diagrama electrico
        esquema_url = self.cliente_rest.obtener_diagrama_remoto(codigo_norm)

        # Evaluacion si existio coincidencia en la base de datos local
        if info_local:
            # Obtencion de la descripcion almacenada
            description = info_local.get("descripcion", "Sin descripción registrada")
            # Obtencion de la categoria del sistema
            categoria = info_local.get("categoria", "Desconocido")
        # Manejo de respuesta cuando el codigo no se encuentra en el repositorio local
        else:
            # Asignacion de texto por defecto ante codigo no registrado
            description = "Código no encontrado en base de datos local"
            # Asignacion de categoria generica por defecto
            categoria = "Genérico"

        # Aplicacion de la regla de negocio para clasificar la severidad
        gravedad = self._determinar_gravedad(codigo_norm)
        # Generacion de texto dinamico con la sugerencia de reparacion
        solucion_sugerida = f"Inspeccionar componentes relacioandos al código {codigo_norm}"

        # Ensamblado e instanciacion final del objeto DTO DTCReporte
        return DTCReporte(
            codigo=codigo_norm,
            description=description,
            categoria=categoria,
            gravedad=gravedad,
            solucion_sugerida=solucion_sugerida,
            esquema_url=esquema_url
        )
