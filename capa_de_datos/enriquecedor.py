"""
Modulo Orquestador de Datos: EnriquecedorDTC
Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importacion de Dict, Optional y Tuple para anotaciones de tipo explicitas
from typing import Dict, Optional, Tuple
# Importacion de la clase GestorBD para consultar datos locales
from capa_de_datos.gestor_bd import GestorBD
# Importacion del ClienteREST para recuperar diagramas remotos
from capa_de_datos.cliente_rest import ClienteREST
# Importacion de la estructura DTO DTCReporte
from capa_de_datos.modelo_reporte import DTCReporte


# Clase principal encargada de combinar informacion local, remota y reglas de negocio
class EnriquecedorDTC:
    """
    Orquesta el enriquecimiento de códigos DTC mediante búsqueda en SQLite,
    decodificación estructural estándar SAE J2012 y consulta remota de diagramas.
    """

    # Diccionario de sistemas principales segun el primer caracter SAE J2012
    SISTEMAS_SAE: Dict[str, str] = {
        "P": "Tren Motriz (Motor/Transmisión)",
        "B": "Carrocería",
        "C": "Chasis",
        "U": "Red",
    }

    # Diccionario de subsistemas del tren motriz segun el tercer caracter (P0xxx / P1xxx)
    SUBSISTEMAS_TREN_MOTRIZ: Dict[str, str] = {
        "0": "Combustible y Aire / Emisiones Auxiliares",
        "1": "Admisión",
        "2": "Combustible",
        "3": "Encendido",
        "4": "Emisiones",
        "5": "Velocidad y Ralentí",
        "6": "Control Electrónico",
        "7": "Transmisión",
        "8": "Transmisión",
        "9": "Transmisión",
        "A": "Propulsión Híbrida",
        "B": "Propulsión Híbrida",
        "C": "Propulsión Híbrida",
    }

    # Inicializador que compone o recibe por inyeccion los servicios de BD y cliente REST
    def __init__(
        self,
        db_path: Optional[str] = None,
        gestor_bd: Optional[GestorBD] = None,
        cliente_rest: Optional[ClienteREST] = None,
    ) -> None:
        # Instanciacion o asignacion del gestor de persistencia SQLite
        self.gestor_bd = gestor_bd if gestor_bd is not None else GestorBD(db_path)
        # Instanciacion o asignacion del cliente para consulta de servicios web
        self.cliente_rest = cliente_rest if cliente_rest is not None else ClienteREST()

    # Metodo interno para categorizar la gravedad del fallo segun el prefijo OBD-II
    def _determinar_gravedad(self, codigo: str) -> str:
        """
        Determina el nivel de severidad ('Alta', 'Media', 'Baja') aplicando reglas
        estándar por prefijo OBD-II cuando un código no tiene severidad explícita.
        """
        # Conversion a mayusculas y limpieza de espacios en blanco
        codigo_norm = codigo.upper().strip()
        # Evaluacion de fallos criticos de encendido (P03/P13), red (U0/U1), airbag (B00) o ABS (C00/C01)
        if (
            codigo_norm.startswith(("P03", "P13", "U0", "U1", "B00", "C00", "C01"))
        ):
            # Asignacion de nivel de gravedad Alta
            return "Alta"
        # Evaluacion si el codigo pertenece a la serie P01/P11 (medicion de aire/combustible)
        elif codigo_norm.startswith(("P01", "P11")):
            # Asignacion de nivel de gravedad Media
            return "Media"
        # Evaluacion si el codigo corresponde a carroceria general (B) o chasis general (C)
        elif codigo_norm.startswith(("B", "C")):
            # Asignacion de nivel de gravedad Baja
            return "Baja"
        # Retorno de gravedad Media como valor por defecto
        return "Media"

    # Metodo interno para decodificar estructuralmente codigos no presentes en SQLite
    def _decodificar_estructura_sae(self, codigo_norm: str) -> Tuple[str, str, str]:
        """
        Analiza los caracteres estándar ISO 15031-6 / SAE J2012 de un código DTC
        no catalogado en SQLite para inferir categoría, descripción y recomendación.

        Returns:
            Tuple[str, str, str]: Tupla (categoria, descripcion, solucion_sugerida).
        """
        # Valida que el codigo cumpla el formato minimo de 5 caracteres OBD-II
        if len(codigo_norm) != 5:
            return (
                "Genérico",
                f"Código no encontrado en base de datos local ({codigo_norm}).",
                f"Inspeccionar componentes relacionados al código {codigo_norm}.",
            )

        # Extraccion de los tres primeros caracteres estructurales
        letra_sistema = codigo_norm[0]
        digito_origen = codigo_norm[1]
        digito_subsistema = codigo_norm[2]

        # Identificacion del sistema principal afectado
        nombre_sistema = self.SISTEMAS_SAE.get(letra_sistema, "Sistema Vehicular")
        # Identificacion de si es estandar SAE (0, 2) o especifico de fabricante OEM (1, 3)
        tipo_origen = (
            "específico del fabricante (OEM)"
            if digito_origen in {"1", "3"}
            else "estándar genérico OBD-II"
        )

        # Determinacion precisa de categoria segun familia
        if letra_sistema == "P":
            categoria = self.SUBSISTEMAS_TREN_MOTRIZ.get(digito_subsistema, "Tren Motriz")
        else:
            categoria = nombre_sistema

        # Construccion de descripcion tecnica estructurada
        descripcion = (
            f"Código {tipo_origen} en {nombre_sistema} — Subsistema {categoria} ({codigo_norm})."
        )
        # Construccion de recomendacion accionable para el taller
        solucion = (
            f"Consultar manual de servicio del fabricante para {codigo_norm} y "
            f"verificar conectores, alimentación y sensores del subsistema {categoria}."
        )

        return (categoria, descripcion, solucion)

    # Construye el objeto DTCReporte integrando la definicion local, la URL remota y la gravedad
    def construir_reporte(self, codigo: str) -> DTCReporte:
        """
        Construye un reporte completo DTCReporte consultando primero SQLite
        y aplicando decodificación estructural SAE como respaldo inteligente.
        """
        # Normalizacion estandar del codigo alfanumerico
        codigo_norm = codigo.upper().strip()
        # Busqueda de la definicion local en el archivo SQLite
        info_local = self.gestor_bd.consultar_codigo(codigo_norm)
        # Consulta remota de disponibilidad del diagrama electrico
        esquema_url = self.cliente_rest.obtener_diagrama_remoto(codigo_norm)

        # Evaluacion si existio coincidencia en la base de datos local
        if info_local:
            # Obtencion de la descripcion almacenada en SQLite
            description = info_local.get("descripcion", "Sin descripción registrada")
            # Obtencion de la categoria del sistema almacenada
            categoria = info_local.get("categoria", "Genérico")
            # Obtencion de la gravedad almacenada o calculo por regla de negocio si falta
            gravedad = info_local.get("gravedad") or self._determinar_gravedad(codigo_norm)
            # Obtencion de la solucion tecnica almacenada o generacion de respaldo
            solucion_sugerida = info_local.get("solucion") or (
                f"Inspeccionar componentes relacionados al código {codigo_norm}."
            )
        # Manejo de respuesta cuando el codigo no se encuentra en el repositorio local
        else:
            # Decodificacion estructural SAE J2012 para evitar falsos alarmismos
            categoria, description, solucion_sugerida = self._decodificar_estructura_sae(codigo_norm)
            # Aplicacion de la regla de negocio para clasificar la severidad
            gravedad = self._determinar_gravedad(codigo_norm)

        # Ensamblado e instanciacion final del objeto DTO DTCReporte
        return DTCReporte(
            codigo=codigo_norm,
            description=description,
            categoria=categoria,
            gravedad=gravedad,
            solucion_sugerida=solucion_sugerida,
            esquema_url=esquema_url,
        )
