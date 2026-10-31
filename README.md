# 🚗 Escáner Automotriz Blar Plus

Sistema de diagnóstico automotriz profesional desarrollado en Python 3.10+ y PySide6 bajo la metodología **Scrumban** (Plazo de 15 días).

## 👥 Equipo de Desarrollo ("BLAR")
* **Mendivil Jiménez José Luis** — Desarrolador
* **Chavarría Mendoza Antonio** — Desarrollador
* **Estrada Loaiza Rogelio** — Desarrollador
* **Polanco Romero Erick** — Desarrollador

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python 3.10+
* **Interfaz Gráfica:** PySide6 (Qt6) & PyQtGraph
* **Comunicación Hardware:** PySerial (Chip ELM327 USB)
* **Persistencia:** SQLite (`Wal33D` Extended) & API REST HTTP

## 🚀 Configuración del Entorno de Desarrollo (Ubuntu Linux)

```bash
# 1. Clonar el repositorio
git clone [https://github.com/biggerihus/blar_plus.git](https://github.com/biggerihus/blar_plus.git)
cd blar_plus

# 2. Permisos de puerto USB (Reiniciar sesión tras ejecutar)
sudo usermod -a -G dialout $USER

# 3. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```
## 🏗️ Arquitectura del Proyecto

```mermaid
flowchart TD
    Root[📁 blar_plus/]
    Root --> C1[📁 interfaz_grafica/]
    C1 --> C1_1[📄 ventana_principal.py]
    C1 --> C1_2[📄 barra_estado.py]
    C1 --> C1_3[📄 lista_dtc.py]
    C1 --> C1_4[📄 dialogo_confirmacion.py]
    C1 --> C1_5[📄 grafico_tiempo_real.py]

    Root --> C2[📁 nucleo_y_controladores/]
    C2 --> C2_1[📄 trabajador_obd.py]
    C2 --> C2_2[📄 controlador_reporte.py]

    Root --> C3[📁 capa_de_datos/]
    C3 --> C3_1[📄 gestor_bd.py]
    C3 --> C3_2[📄 enriquecedor.py]
    C3 --> C3_3[📄 cliente_rest.py]
    C3 --> C3_4[📄 modelo_reporte.py]
    C3 --> C3_5[💾 dtc_database.db]

    Root --> C4[📁 abstraccion_de_hardware/]
    C4 --> C4_1[📄 i_adaptador_obd.py]
    C4 --> C4_2[📄 adaptador_elm327.py]
    C4 --> C4_3[📄 adaptador_simulador.py]
    C4 --> C4_4[📄 estrategias_protocolo.py]
```

## 🔄 Flujo de Importaciones entre Capas

```mermaid
flowchart TD
    GUI[Capa 1: interfaz_grafica] -->|Importa| CTRL[Capa 2: nucleo_y_controladores]
    CTRL -->|Importa| DATA[Capa 3: capa_de_datos]
    CTRL -->|Importa| HW[Capa 4: abstraccion_de_hardware]
```
