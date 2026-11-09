"""
Módulo para Inicializar la Base de Datos SQLite para Blar Plus.

Crea la estructura de la base de datos local y llena la tabla 'dtc_definitions'
con códigos de diagnóstico iniciales de prueba alineaados con GestorBD.

Autor: Equipo Blar Plus
Capa: Capa de Datos / Capa 3
"""

# Importación del módulo os para creación de directorios en el sistema
import os
# Importación del módulo sqlite3 para administración de la base de datos local
import sqlite3


def inicializar_bd(db_path: str = "capa_de_datos/dtc_database.db") -> None:
    """
    Recrea la tabla dtc_definitions con el campo 'type' e inserta registros base.

    Args:
        db_path (str): Ruta relativa o absoluta del archivo de base de datos SQLite.
    """
    # Creación del directorio de destino si no existe en el sistema de archivos
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Conexión con el archivo SQLite
    conn = sqlite3.connect(db_path)
    # Creación del cursor para ejecución de comandos SQL
    cursor = conn.cursor()

    # Eliminación de la tabla previa en caso de tener un esquema antiguo sin la columna 'type'
    cursor.execute("DROP TABLE IF EXISTS dtc_definitions")

    # Creación de la tabla estandarizada con la columna 'type' que consulta GestorBD
    cursor.execute("""
        CREATE TABLE dtc_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL
        )
    """)

    # Registros iniciales de prueba para poblar el catálogo local
    codigos_iniciales = [
        ("P0300", "Fallo de encendido aleatorio en múltiples cilindros.", "Encendido"),
        ("P0113", "Sensor de temperatura del aire de admisión (IAT) voltaje alto.", "Admisión"),
        ("P0420", "Eficiencia del sistema catalítico por debajo del umbral.", "Emisiones"),
        ("P0171", "Sistema demasiado pobre (Banco 1).", "Combustible"),
        ("B0001", "Circuito de control del airbag del conductor.", "Carrocería"),
        ("U0100", "Pérdida de comunicación con el ECM/PCM A.", "Red"),
    ]

    # Inserción masiva de registros en la tabla
    cursor.executemany("""
        INSERT INTO dtc_definitions (code, description, type)
        VALUES (?, ?, ?)
    """, codigos_iniciales)

    # Confirmación de la transacción
    conn.commit()
    # Cierre de la conexión
    conn.close()

    # Notificación de éxito en consola
    print(f"Base de datos inicializada correctamente en: {db_path}")


# Punto de ejecución directa del script
if __name__ == "__main__":
    inicializar_bd()
