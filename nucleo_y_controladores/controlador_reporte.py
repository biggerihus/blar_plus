"""
Módulo de Control de Reportes y Transformación de Datos para Blar Plus.

Proporciona la lógica de negocio para consolidar diagnósticos OBD-II,
transformar lecturas crudas en Objetos de Transferencia de Datos (DTOs)
mediante el servicio EnriquecedorDTC y estructurar reportes para la GUI.

Autor: Erick Polanco Romero
Capa: Núcleo y Controladores / Capa 2
"""

# Importacion del decorador dataclass para la estructuracion automatica de objetos de datos
from dataclasses import dataclass
# Importacion de tipos Any, Dict, List y Optional para las anotaciones explicitas de tipo
from typing import Any, Dict, List, Optional

# Importacion del orquestador de datos de la Capa 3 para consultar y enriquecer DTCs
from capa_de_datos.enriquecedor import EnriquecedorDTC


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

    Actúa como puente de negocio entre los datos recibidos del bus OBD,
    el repositorio local SQLite en Capa 3 y los widgets visuales de la GUI.
    """

    # Inicializador de la clase controlador con inyeccion opcional de EnriquecedorDTC
    def __init__(self, enriquecedor: Optional[EnriquecedorDTC] = None) -> None:
        """
        Inicializa el controlador, el servicio de enriquecimiento DTC y el historial.

        Args:
            enriquecedor (Optional[EnriquecedorDTC]): Instancia de EnriquecedorDTC.
                Si es None, crea una instancia conectada a la base de datos SQLite local.
        """
        # Instanciacion o asignacion del servicio de enriquecimiento de Capa 3
        self.enriquecedor: EnriquecedorDTC = (
            enriquecedor if enriquecedor is not None else EnriquecedorDTC()
        )
        # Inicializacion de la lista vacia para guardar el historial de reportes
        self._historial_reportes: List[Dict[str, Any]] = []

    # Metodo para procesar una lista de cadenas de codigos crudos y retornar objetos DTCDTO
    def procesar_dtcs_raw(self, dtcs_raw: List[str]) -> List[DTCDTO]:
        """
        Transforma una lista de cadenas de texto crudas en Objetos DTCDTO estructurados
        consultando la base de datos SQLite y las reglas de negocio de EnriquecedorDTC.

        Args:
            dtcs_raw (List[str]): Lista de códigos crudos leídos (ej. ["P0300", "P0171"]).

        Returns:
            List[DTCDTO]: Colección de objetos DTO listos para la GUI (`ListaDTCWidget`).
        """
        # Creacion de la lista vacia receptora de objetos DTO
        dtos: List[DTCDTO] = []

        # Recorrido de cada codigo alfanumerico crudo en la lista recibida
        for codigo in dtcs_raw:
            # Consulta al orquestador de Capa 3 para obtener el reporte enriquecido
            reporte = self.enriquecedor.construir_reporte(codigo)

            # Mapeo del objeto DTCReporte (Capa 3) al objeto DTCDTO (Capa 2 / GUI)
            dto = DTCDTO(
                codigo=reporte.codigo,
                categoria=reporte.categoria,
                gravedad=reporte.gravedad,
                descripcion=reporte.description,
                solucion=reporte.solucion_sugerida,
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
