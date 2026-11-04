"""
Modulo de Persistencia SQLite: GestorBD
Consultas Locales 
"""

import sqlite3
from typing import Optional, Dict, Any

class GestorBD:
    def __init__(self, db_path: str = "capa_de_datos/dtc_database.db"):
        self.db_path = db_path

def consultar_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
    query = "Select code, description, category From dtc_codes WHERE code = ?"
    try:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (codigo,))
            fila = cursor.fetchone()
            if fila:
                return {
                    "codigo": fila[0],
                    "descripcion": fila[1],
                    "categoria": fila[2]
                }
                return None 
    except sqlite3.Error as err:
                    print(f"Error al consultar SQLite: {err}")
                    return None