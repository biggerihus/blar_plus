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
