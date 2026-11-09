"""
Módulo de Persistencia SQLite: GestorBD.
Gestiona las consultas locales a dtc_database.db.
Autor: Chavarria Mendoza Antonio
Capa: Capa de Datos / Capa 3
"""

# Importacion del modulo sqlite3 para interactuar con la base de datos local
import sqlite3
# Importacion de tipos para especificacion explicita de firmas
from typing import Optional, Dict, Any

# Clase responsable del acceso y lectura de la base de datos SQLite local
class GestorBD:
    # Inicializador de la clase especificando la ruta predeterminada de la base de datos
    def __init__(self, db_path: str = "capa_de_datos/dtc_database.db"):
        # Almacenamiento de la ruta de la base de datos en una variable de instancia
        self.db_path = db_path

    # Consulta las propiedades de un codigo DTC almacenado en la tabla dtc_definitions
    def consultar_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Consulta el código en dtc_definitions obteniendo code, description y type.
        """
        # Sentencia SQL parametrizada para evitar inyecciones SQL
        query = "SELECT code, description, type FROM dtc_definitions WHERE code = ?"
        # Bloque try para el manejo de excepciones de base de datos
        try:
            # Creacion y apertura administrada de la conexion con la base de datos
            with sqlite3.connect(self.db_path) as conn:
                # Obtencion del objeto cursor para ejecutar la consulta
                cursor = conn.cursor()
                # Ejecucion del comando SQL pasando el codigo formateado en una tupla
                cursor.execute(query, (codigo,))
                # Extraccion del primer resultado encontrado
                fila = cursor.fetchone()
                # Evaluacion si se recupero una fila coincidente
                if fila:
                    # Devolucion de la fila mapeada en un diccionario estructurado
                    return {
                        "codigo": fila[0],
                        "descripcion": fila[1],
                        "categoria": fila[2]
                    }
                # Retorno nulo si el codigo no existe en la tabla local
                return None
        # Captura de errores propios de la libreria sqlite3
        except sqlite3.Error as err:
            # Impresion en consola del mensaje detallado de error
            print(f"Error al consultar SQLite: {err}")
            # Retorno nulo tras producirse una falla
            return None
