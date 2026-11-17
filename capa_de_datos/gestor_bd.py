"""
Módulo de Persistencia SQLite: GestorBD.

Gestiona la auto-inicialización, consulta parametrizada y almacenamiento en caché
local de códigos de diagnóstico en dtc_database.db.

Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importación del módulo os para verificación de existencia de archivos en disco
import os
# Importación del módulo sqlite3 para interactuar con la base de datos local
import sqlite3
# Importación de tipos para especificación explícita de firmas
from typing import Any, Dict, Optional

# Importación de utilidades de inicialización y resolución segura de rutas
from capa_de_datos.inicializar_db import inicializar_bd, resolver_ruta_bd


# Clase responsable del acceso, lectura, caché y validación de la base de datos SQLite local
class GestorBD:
    """
    Administra el ciclo de vida y las operaciones CRUD sobre dtc_database.db.
    """

    # Columnas requeridas en el esquema actualizado de la tabla dtc_definitions
    COLUMNAS_REQUERIDAS = {"code", "description", "type", "severity", "solution"}

    def __init__(self, db_path: Optional[str] = None, auto_init: bool = True):
        """
        Inicializa el gestor de base de datos y verifica que el esquema esté listo.

        Args:
            db_path (Optional[str]): Ruta a la base de datos SQLite o ':memory:'.
                                     Si es None, resuelve automáticamente la ruta del proyecto.
            auto_init (bool): Si es True, crea o actualiza automáticamente la BD si falta o está vacía.
        """
        # Almacena la ruta efectiva de la base de datos en una variable de instancia
        self.db_path = db_path if db_path is not None else resolver_ruta_bd()

        # Si la auto-inicialización está habilitada, garantiza que la tabla exista y esté poblada
        if auto_init:
            self._asegurar_base_datos()

    def _asegurar_base_datos(self) -> None:
        """
        Verifica que el archivo SQLite exista, tenga las columnas actuales y contenga datos.
        Si detecta una BD inexistente, vacía o con esquema antiguo, la regenera automáticamente.
        """
        # Si es base en memoria o el archivo físico aún no existe, inicializa de inmediato
        if self.db_path == ":memory:" or not os.path.exists(self.db_path):
            inicializar_bd(db_path=self.db_path, forzar_reinicio=True)
            return

        # Inspecciona la estructura actual de la base de datos existente
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Consulta los metadatos de columnas de la tabla dtc_definitions
                cursor.execute("PRAGMA table_info(dtc_definitions)")
                columnas_actuales = {fila[1] for fila in cursor.fetchall()}

                # Si faltan columnas del esquema profesional, reconstruye la tabla
                if not self.COLUMNAS_REQUERIDAS.issubset(columnas_actuales):
                    inicializar_bd(db_path=self.db_path, forzar_reinicio=True)
                    return

                # Verifica que la tabla no se encuentre vacía
                cursor.execute("SELECT COUNT(*) FROM dtc_definitions")
                total = int(cursor.fetchone()[0])
                if total == 0:
                    inicializar_bd(db_path=self.db_path, forzar_reinicio=True)
        except sqlite3.Error:
            # Ante cualquier archivo corrupto, regenera la base de datos limpia
            inicializar_bd(db_path=self.db_path, forzar_reinicio=True)

    def consultar_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Consulta un código DTC en dtc_definitions obteniendo toda su información técnica.

        Args:
            codigo (str): Código de diagnóstico OBD-II (ej. 'P0300').

        Returns:
            Optional[Dict[str, Any]]: Diccionario con codigo, descripcion, categoria,
                                      gravedad y solucion; o None si no existe.
        """
        # Normaliza el código de entrada eliminando espacios y convirtiendo a mayúsculas
        codigo_normalizado = codigo.strip().upper()

        # Sentencia SQL parametrizada para evitar inyecciones SQL
        query = """
            SELECT code, description, type, severity, solution
            FROM dtc_definitions
            WHERE code = ?
        """
        # Bloque try para el manejo controlado de excepciones de base de datos
        try:
            # Creación y apertura administrada de la conexión con la base de datos
            with sqlite3.connect(self.db_path) as conn:
                # Obtención del objeto cursor para ejecutar la consulta
                cursor = conn.cursor()
                # Ejecución del comando SQL pasando el código formateado en una tupla
                cursor.execute(query, (codigo_normalizado,))
                # Extracción del primer resultado encontrado
                fila = cursor.fetchone()
                # Evaluación si se recuperó una fila coincidente
                if fila:
                    # Devolución de la fila mapeada en un diccionario estructurado
                    return {
                        "codigo": fila[0],
                        "descripcion": fila[1],
                        "categoria": fila[2],
                        "gravedad": fila[3],
                        "solucion": fila[4],
                    }
                # Retorno nulo si el código no existe en la tabla local
                return None
        # Captura de errores propios de la librería sqlite3
        except sqlite3.Error as err:
            # Impresión en consola del mensaje detallado de error
            print(f"Error al consultar SQLite: {err}")
            # Retorno nulo tras producirse una falla
            return None

    def guardar_codigo(
        self,
        codigo: str,
        descripcion: str,
        categoria: str,
        gravedad: str = "Media",
        solucion: str = "",
    ) -> bool:
        """
        Inserta o actualiza un código DTC en SQLite (utilizado para caché de lectura remota).

        Args:
            codigo (str): Identificador del código DTC (ej. 'P1456').
            descripcion (str): Descripción técnica de la falla.
            categoria (str): Subsistema o familia del código.
            gravedad (str): Nivel de severidad ('Alta', 'Media', 'Baja').
            solucion (str): Procedimiento recomendado de diagnóstico o reparación.

        Returns:
            bool: True si se guardó correctamente, False en caso de error.
        """
        # Normaliza el código DTC antes de persistirlo
        codigo_normalizado = codigo.strip().upper()
        # Sentencia SQL parametrizada para inserción o actualización atómica
        query = """
            INSERT OR REPLACE INTO dtc_definitions (code, description, type, severity, solution)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            # Abre conexión administrada que realiza commit automático al finalizar sin errores
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (codigo_normalizado, descripcion, categoria, gravedad, solucion),
                )
            return True
        except sqlite3.Error as err:
            print(f"Error al guardar código en SQLite: {err}")
            return False

    def contar_codigos(self) -> int:
        """
        Devuelve la cantidad total de códigos DTC almacenados actualmente en SQLite.

        Returns:
            int: Número de registros en dtc_definitions (0 si ocurre algún error).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM dtc_definitions")
                return int(cursor.fetchone()[0])
        except sqlite3.Error:
            return 0
