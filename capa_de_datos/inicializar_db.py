"""
Módulo para Inicializar la Base de Datos SQLite para Blar Plus.

Crea la estructura actualizada de la base de datos local y llena la tabla
'dtc_definitions' desde el catálogo maestro JSON o mediante registros base
de respaldo, asegurando compatibilidad con rutas en desarrollo y empaquetado.

Autor: Equipo Blar Plus
Capa: Capa de Datos / Capa 3
"""

# Importación del módulo json para lectura del catálogo estructurado de códigos DTC
import json
# Importación del módulo os para gestión de rutas y creación de directorios
import os
# Importación del módulo sqlite3 para administración de la base de datos local
import sqlite3
# Importación del módulo sys para detectar ejecución empaquetada (PyInstaller)
import sys
# Importación de Path para resolución multiplataforma limpia de rutas del proyecto
from pathlib import Path
# Importación de tipos para especificación explícita de firmas
from typing import List, Optional, Tuple


# Catálogo mínimo de respaldo en caso de ejecutarse antes de generar catalogo_dtc.json
CODIGOS_RESPALDO: List[Tuple[str, str, str, str, str]] = [
    (
        "P0300",
        "Fallo de encendido aleatorio o en múltiples cilindros detectado.",
        "Encendido",
        "Alta",
        "Revisar bujías, bobinas de encendido, cables de alta tensión, inyectores y presión de combustible.",
    ),
    (
        "P0113",
        "Señal alta en el circuito del sensor de temperatura del aire de admisión (IAT).",
        "Admisión",
        "Media",
        "Inspeccionar el conector del sensor IAT, verificar continuidad del cableado y reemplazar el sensor si está abierto.",
    ),
    (
        "P0420",
        "Eficiencia del sistema catalítico por debajo del umbral permitido (Banco 1).",
        "Emisiones",
        "Media",
        "Verificar fugas en el escape, comprobar lectura de sensores de oxígeno (O2) y evaluar estado del convertidor catalítico.",
    ),
    (
        "P0171",
        "Mezcla de combustible demasiado pobre en el Banco 1.",
        "Combustible",
        "Media",
        "Revisar fugas de vacío en admisión, limpiar sensor MAF y comprobar presión de la bomba de combustible.",
    ),
    (
        "B0001",
        "Falla en el circuito de despliegue frontal del airbag del conductor (Etapa 1).",
        "Carrocería",
        "Alta",
        "Desconectar batería, revisar conector bajo el volante, resorte reloj (clock spring) y módulo SRS.",
    ),
    (
        "U0100",
        "Pérdida de comunicación con el módulo de control del motor/tren motriz (ECM/PCM A).",
        "Red",
        "Alta",
        "Verificar alimentación y tierras del ECM, fusibles principales y resistencia terminal del bus CAN (60 Ohmios).",
    ),
]


def resolver_ruta_recurso(ruta_relativa: str) -> str:
    """
    Resuelve la ruta absoluta hacia un recurso de solo lectura (ej. catalogo_dtc.json),
    soportando tanto ejecución normal en Python como binarios empaquetados.

    Args:
        ruta_relativa (str): Ruta relativa desde la raíz del proyecto.

    Returns:
        str: Ruta absoluta lista para lectura.
    """
    # Verifica si la aplicación corre congelada mediante PyInstaller
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Obtiene el directorio temporal donde PyInstaller extrae los recursos
        base_path = Path(sys._MEIPASS)
    else:
        # Obtiene la carpeta raíz del proyecto subiendo un nivel desde capa_de_datos
        base_path = Path(__file__).resolve().parent.parent

    # Retorna la ruta completa normalizada como cadena de texto
    return str(base_path / ruta_relativa)


def resolver_ruta_bd(ruta_relativa: str = "capa_de_datos/dtc_database.db") -> str:
    """
    Resuelve la ruta absoluta hacia una ubicación con permisos de escritura para SQLite.

    Args:
        ruta_relativa (str): Ruta relativa esperada de la base de datos.

    Returns:
        str: Ruta absoluta donde se leerá y escribirá el archivo .db.
    """
    # Si la aplicación está empaquetada, ubica la BD junto al ejecutable para poder escribir
    if getattr(sys, "frozen", False):
        # Obtiene el directorio que contiene el archivo ejecutable
        base_path = Path(sys.executable).resolve().parent
    else:
        # En desarrollo utiliza la carpeta raíz del proyecto
        base_path = Path(__file__).resolve().parent.parent

    # Retorna la ruta completa normalizada como cadena de texto
    return str(base_path / ruta_relativa)


def _cargar_registros_desde_json(json_path: str) -> List[Tuple[str, str, str, str, str]]:
    """
    Lee y valida los registros de códigos DTC almacenados en un archivo JSON maestro.

    Args:
        json_path (str): Ruta al archivo catalogo_dtc.json.

    Returns:
        List[Tuple[str, str, str, str, str]]: Lista de tuplas listas para SQLite.
    """
    # Verifica si el archivo JSON existe en el sistema de archivos
    if not os.path.exists(json_path):
        # Retorna lista vacía para activar el respaldo interno
        return []

    # Abre el archivo JSON con codificación UTF-8 para preservar acentos técnicos
    with open(json_path, "r", encoding="utf-8") as archivo:
        # Deserializa el contenido JSON a estructuras nativas de Python
        datos = json.load(archivo)

    # Lista acumuladora de tuplas validadas
    registros: List[Tuple[str, str, str, str, str]] = []

    # Recorre cada entrada del catálogo JSON
    for item in datos:
        # Extrae y normaliza el código DTC a mayúsculas sin espacios
        codigo = str(item.get("codigo", "")).strip().upper()
        # Extrae la descripción técnica del código
        descripcion = str(item.get("descripcion", "")).strip()
        # Extrae la categoría o subsistema afectado
        categoria = str(item.get("categoria", "Genérico")).strip()
        # Extrae el nivel de gravedad asignado
        gravedad = str(item.get("gravedad", "Media")).strip()
        # Extrae la acción correctiva sugerida
        solucion = str(item.get("solucion", "Realizar inspección técnica del subsistema afectado.")).strip()

        # Solo incorpora registros que cuenten con código y descripción válidos
        if codigo and descripcion:
            registros.append((codigo, descripcion, categoria, gravedad, solucion))

    # Retorna la colección lista para inserción masiva
    return registros


def inicializar_bd(
    db_path: Optional[str] = None,
    json_path: Optional[str] = None,
    forzar_reinicio: bool = True,
) -> int:
    """
    Crea o actualiza la tabla dtc_definitions con el esquema completo e inserta el catálogo.

    Args:
        db_path (Optional[str]): Ruta del archivo SQLite o ':memory:'. Si es None, se resuelve automáticamente.
        json_path (Optional[str]): Ruta del archivo JSON maestro. Si es None, busca capa_de_datos/catalogo_dtc.json.
        forzar_reinicio (bool): Si es True, recrea la tabla desde cero para evitar esquemas obsoletos.

    Returns:
        int: Cantidad total de códigos almacenados en la base de datos.
    """
    # Determina la ruta efectiva de la base de datos SQLite
    ruta_bd = db_path if db_path is not None else resolver_ruta_bd()
    # Determina la ruta efectiva del catálogo JSON maestro
    ruta_json = json_path if json_path is not None else resolver_ruta_recurso("capa_de_datos/catalogo_dtc.json")

    # Crea el directorio padre únicamente si la BD reside en disco y tiene carpeta contenedora
    if ruta_bd != ":memory:":
        directorio = os.path.dirname(ruta_bd)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

    # Intenta cargar los registros desde el catálogo JSON maestro
    registros = _cargar_registros_desde_json(ruta_json)
    # Si no existe JSON todavía, utiliza el catálogo mínimo de respaldo
    if not registros:
        registros = CODIGOS_RESPALDO

    # Establece la conexión con el motor SQLite
    conn = sqlite3.connect(ruta_bd)
    # Crea el cursor para ejecución de sentencias DDL y DML
    cursor = conn.cursor()

    # Si se solicita reinicio limpio, elimina la tabla anterior con esquema antiguo
    if forzar_reinicio:
        cursor.execute("DROP TABLE IF EXISTS dtc_definitions")

    # Crea la tabla estandarizada con soporte completo de categoría, gravedad y solución
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dtc_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'Media',
            solution TEXT NOT NULL DEFAULT ''
        )
    """)

    # Inserta o actualiza masivamente todos los registros en una sola transacción
    cursor.executemany(
        """
        INSERT OR REPLACE INTO dtc_definitions (code, description, type, severity, solution)
        VALUES (?, ?, ?, ?, ?)
        """,
        registros,
    )

    # Confirma los cambios de forma atómica en el archivo de base de datos
    conn.commit()
    # Obtiene el conteo final de registros almacenados
    cursor.execute("SELECT COUNT(*) FROM dtc_definitions")
    total_registros = int(cursor.fetchone()[0])
    # Cierra la conexión liberando el recurso
    conn.close()

    # Notifica en consola el resultado de la operación
    print(f"Base de datos inicializada correctamente en: {ruta_bd} ({total_registros} códigos)")
    # Retorna el total de códigos cargados
    return total_registros


# Punto de ejecución directa del script desde terminal
if __name__ == "__main__":
    inicializar_bd()
