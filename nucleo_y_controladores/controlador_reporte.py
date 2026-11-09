"""
Módulo de Control de Reportes y Transformación de Datos para Blar Plus.

Proporciona la lógica de negocio para consolidar diagnósticos OBD-II,
transformar lecturas crudas en Objetos de Transferencia de Datos (DTOs)
y estructurar reportes completos para la capa de presentación.

Autor: Erick Polanco Romero
Capa: Núcleo y Controladores / Capa 2
"""

# Importacion del decorador dataclass para la estructuracion automatica de objetos de datos
from dataclasses import dataclass
# Importacion de tipos Any, Dict y List para las anotaciones explicitas de tipo
from typing import Any, Dict, List


# Definicion de la clase DTO para transferir datos estructurados de DTC a la interfaz grafica
@dataclass
class DTCDTO:
    """
    Objeto de Transferencia de Datos (DTO) para la representación estructurada de un DTC.

    Atributos:
        codigo (str): Código alfanumérico estándar OBD-II (ej. 'P0300').
        categoria (str): Subsistema del vehículo afectado (ej. 'Encendido', 'Admisión').
        gravedad (str): Nivel de severidad del fallo ('Alta', 'Media', 'Baja').
        descripcion (str): Explicación técnica detallada de la anomalía.
        solucion (str): Recomendación o paso correctivo sugerido.
    """

    # Codigo alfanumerico estandar OBD-II
    codigo: str
    # Categoria o subsistema afectado en el vehiculo
    categoria: str
    # Nivel de gravedad o severidad de la falla
    gravedad: str
    # Descripcion tecnica detallada de la falla
    descripcion: str
    # Sugerencia de reparacion o diagnostico
    solucion: str


# Clase principal de control encargada de transformar tramas y armar reportes
class ControladorReporte:
    """
    Gestiona la transformación de datos crudos a DTOs y la generación de reportes.

    Actúa como puente de negocio entre los datos recibidos del bus OBD
    y los widgets visuales de la interfaz de usuario.
    """

    # Diccionario estatico de catalogo de codigos DTC con sus metadatos asociados
    CATALOGO_DTC: Dict[str, Dict[str, str]] = {
        # Definicion de metadatos para el codigo de falla P0300
        "P0300": {
            "categoria": "Encendido",
            "gravedad": "Alta",
            "descripcion": "Fallo de encendido aleatorio en múltiples cilindros.",
            "solucion": "Revisar bujías, bobinas y presión de combustible.",
        },
        # Definicion de metadatos para el codigo de falla P0113
        "P0113": {
            "categoria": "Admisión",
            "gravedad": "Media",
            "descripcion": "Sensor de temperatura del aire de admisión (IAT) voltaje alto.",
            "solucion": "Verificar cableado y conector del sensor IAT.",
        },
        # Definicion de metadatos para el codigo de falla P0420
        "P0420": {
            "categoria": "Emisiones",
            "gravedad": "Baja",
            "descripcion": "Eficiencia del sistema catalítico por debajo del umbral.",
            "solucion": "Inspeccionar fugas en el escape o estado del convertidor.",
        },
    }

    # Inicializador de la clase controlador
    def __init__(self) -> None:
        """Inicializa el controlador y la lista en memoria del historial de diagnósticos."""
        # Inicializacion de la lista vacia para guardar el historial de reportes
        self._historial_reportes: List[Dict[str, Any]] = []

    # Metodo para procesar una lista de cadenas de codigos crudos y retornar objetos DTCDTO
    def procesar_dtcs_raw(self, dtcs_raw: List[str]) -> List[DTCDTO]:
        """
        Transforma una lista de cadenas de texto crudas en Objetos DTCDTO estructurados.

        Si un código no se encuentra en el catálogo local, genera un DTO genérico
        de respaldo (fallback) con severidad 'Alta'.

        Args:
            dtcs_raw (List[str]): Lista de códigos crudos leídos (ej. ["P0300", "P0113"]).

        Returns:
            List[DTCDTO]: Colección de objetos DTO listos para la GUI (`ListaDTCWidget`).
        """
        # Creacion de la lista vacia receptora de objetos DTO
        dtos: List[DTCDTO] = []

        # Recorrido de cada codigo alfanumerico crudo en la lista recibida
        for codigo in dtcs_raw:
            # Consulta en el catalogo local con diccionario de respaldo por defecto si no existe
            info = self.CATALOGO_DTC.get(
                codigo,
                {
                    "categoria": "General",
                    "gravedad": "Alta",
                    "descripcion": f"Código de falla no catalogado ({codigo}).",
                    "solucion": "Realizar diagnóstico detallado con escáner avanzado.",
                },
            )

            # Instanciacion del objeto DTO con la informacion recuperada o por defecto
            dto = DTCDTO(
                codigo=codigo,
                categoria=info["categoria"],
                gravedad=info["gravedad"],
                descripcion=info["descripcion"],
                solucion=info["solucion"],
            )
            # Adicion del objeto DTO a la lista de salida
            dtos.append(dto)

        # Devolucion del conjunto de DTOs construidos
        return dtos

    # Metodo para estructurar un resumen general del reporte de fallas
    def generar_reporte(self, dtcs: List[str]) -> Dict[str, Any]:
        """
        Genera una estructura formal de reporte a partir de una lista de códigos DTC.

        Args:
            dtcs (List[str]): Lista de códigos DTC leídos.

        Returns:
            Dict[str, Any]: Resumen estructurado con el estado general y total de fallas.
        """
        # Evaluacion ternaria para determinar el estado de severidad del vehiculo
        estado_severidad: str = "Crítico" if dtcs else "Sin Fallas"

        # Construccion del diccionario con las metricas generales del reporte
        reporte: Dict[str, Any] = {
            "total_fallas": len(dtcs),
            "codigos": dtcs,
            "estado": estado_severidad,
        }

        # Registro del reporte generado en la lista de historial
        self._historial_reportes.append(reporte)
        # Retorno del diccionario del reporte
        return reporte

    # Metodo para consultar las copias de los reportes acumulados
    def obtener_historial(self) -> List[Dict[str, Any]]:
        """
        Devuelve una copia del historial de reportes acumulados en la sesión.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios de reportes generados.
        """
        # Devolucion de una copia de la lista de historial para evitar mutaciones externas
        return list(self._historial_reportes)
