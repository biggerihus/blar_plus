"""
Módulo de Control de Reportes y Transformación de Datos para Blar Plus.

Proporciona la lógica de negocio para consolidar diagnósticos OBD-II,
transformar lecturas crudas en Objetos de Transferencia de Datos (DTOs)
y estructurar reportes completos para la capa de presentación.

Autor: Erick Polanco Romero
"""

from dataclasses import dataclass
from typing import Any, Dict, List


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

    codigo: str
    categoria: str
    gravedad: str
    descripcion: str
    solucion: str


class ControladorReporte:
    """
    Gestiona la transformación de datos crudos a DTOs y la generación de reportes.

    Actúa como puente de negocio entre los datos recibidos del bus OBD
    y los widgets visuales de la interfaz de usuario.
    """

    # Catálogo en memoria para el mapeo de códigos crudos a objetos DTO enriquecidos
    CATALOGO_DTC: Dict[str, Dict[str, str]] = {
        "P0300": {
            "categoria": "Encendido",
            "gravedad": "Alta",
            "descripcion": "Fallo de encendido aleatorio en múltiples cilindros.",
            "solucion": "Revisar bujías, bobinas y presión de combustible.",
        },
        "P0113": {
            "categoria": "Admisión",
            "gravedad": "Media",
            "descripcion": "Sensor de temperatura del aire de admisión (IAT) voltaje alto.",
            "solucion": "Verificar cableado y conector del sensor IAT.",
        },
        "P0420": {
            "categoria": "Emisiones",
            "gravedad": "Baja",
            "descripcion": "Eficiencia del sistema catalítico por debajo del umbral.",
            "solucion": "Inspeccionar fugas en el escape o estado del convertidor.",
        },
    }

    def __init__(self) -> None:
        """Inicializa el controlador y la lista en memoria del historial de diagnósticos."""
        self._historial_reportes: List[Dict[str, Any]] = []

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
        dtos: List[DTCDTO] = []

        for codigo in dtcs_raw:
            # Busca los metadatos del código o aplica la plantilla por defecto si no existe
            info = self.CATALOGO_DTC.get(
                codigo,
                {
                    "categoria": "General",
                    "gravedad": "Alta",
                    "descripcion": f"Código de falla no catalogado ({codigo}).",
                    "solucion": "Realizar diagnóstico detallado con escáner avanzado.",
                },
            )

            # Construcción de la instancia DTO
            dto = DTCDTO(
                codigo=codigo,
                categoria=info["categoria"],
                gravedad=info["gravedad"],
                descripcion=info["descripcion"],
                solucion=info["solucion"],
            )
            dtos.append(dto)

        return dtos

    def generar_reporte(self, dtcs: List[str]) -> Dict[str, Any]:
        """
        Genera una estructura formal de reporte a partir de una lista de códigos DTC.

        Args:
            dtcs (List[str]): Lista de códigos DTC leídos.

        Returns:
            Dict[str, Any]: Resumen estructurado con el estado general y total de fallas.
        """
        estado_severidad: str = "Crítico" if dtcs else "Sin Fallas"

        reporte: Dict[str, Any] = {
            "total_fallas": len(dtcs),
            "codigos": dtcs,
            "estado": estado_severidad,
        }

        self._historial_reportes.append(reporte)
        return reporte

    def obtener_historial(self) -> List[Dict[str, Any]]:
        """
        Devuelve una copia del historial de reportes acumulados en la sesión.

        Returns:
            List[Dict[str, Any]]: Lista de diccionarios de reportes generados.
        """
        return list(self._historial_reportes)
