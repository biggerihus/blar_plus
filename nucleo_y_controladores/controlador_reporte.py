"""
Módulo de Control de Reportes para Blar Plus.

Proporciona la lógica de negocio para consolidar los diagnósticos OBD-II,
estructurar la información capturada por los trabajadores de concurrencia
y preparar reportes detallados para su persistencia o presentación gráfica.

Autor: Erick Polanco Romero
"""

from typing import Any, Dict, List


class ControladorReporte:
    """
    Gestiona la generación, formateo y procesamiento de reportes de diagnóstico.

    Actúa como intermediario entre la capa de control de hardware/datos y los
    módulos de presentación o almacenamiento del sistema Blar Plus.

    Atributos:
        _historial_reportes (List[Dict[str, Any]]): Registro en memoria de todos
            los reportes procesados durante la sesión activa.
    """

    def __init__(self) -> None:
        """
        Inicializa una nueva instancia del controlador de reportes.

        Configura la estructura básica en memoria para almacenar el historial de diagnósticos.
        """
        self._historial_reportes: List[Dict[str, Any]] = []

    def generar_reporte(self, dtcs: List[str]) -> Dict[str, Any]:
        """
        Genera una estructura formal de reporte a partir de una lista de códigos DTC.

        Args:
            dtcs (List[str]): Lista de códigos de falla de diagnóstico leídos
                desde la ECU del vehículo (ej. ["P0300", "P0171"]).

        Returns:
            Dict[str, Any]: Diccionario estructurado con la información del reporte,
                incluyendo total de fallas, lista de códigos y el estado de gravedad.

        Example:
            >>> controlador = ControladorReporte()
            >>> controlador.generar_reporte(["P0300"])
            {'total_fallas': 1, 'codigos': ['P0300'], 'estado': 'Crítico'}
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
        Obtiene la lista completa de reportes generados en la sesión actual.

        Returns:
            List[Dict[str, Any]]: Copia del historial de reportes acumulados.
        """
        return list(self._historial_reportes)
