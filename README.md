# 🚗 Escáner Automotriz Blar Plus

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-green?logo=qt&logoColor=white)
![PyQtGraph](https://img.shields.io/badge/Plotting-PyQtGraph-orange)
![SQLite](https://img.shields.io/badge/Database-SQLite3-blueviolet?logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-22%2F22%20Passed-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Sistema profesional de diagnóstico automotriz OBD-II desarrollado en Python 3.10+ y PySide6. Implementa una **arquitectura desacoplada de 4 capas** con muestreo en tiempo real a 10 Hz mediante comunicación serie (dispositivos USB ELM327) o emulación simulada con física vehicular correlacionada, cumplimiento de protocolos estándar **SAE J1979 / ISO 15031-5** y resiliencia ante fallos físicos de hardware. Desarrollado bajo la metodología **Scrumban**.

---

## 👥 Equipo de Desarrollo ("BLAR")

| Desarrollador | Rol / Capa Asignada | Módulo Principal |
| :--- | :--- | :--- |
| **Mendivil Jiménez José Luis** | Capa 4 — Abstracción de Hardware (HAL) | `abstraccion_de_hardware/` |
| **Chavarría Mendoza Antonio** | Capa 3 — Persistencia y Datos | `capa_de_datos/` |
| **Polanco Romero Erick** | Capa 2 — Núcleo y Concurrencia | `nucleo_y_controladores/` |
| **Estrada Loaiza Rogelio** | Capa 1 — Interfaz Gráfica (GUI) | `interfaz_grafica/` |

---

## 🎯 Objetivos Planeados vs. Mejoras Implementadas

### 📌 Objetivos Planeados Iniciales
* [x] **Arquitectura Multicapa:** Separación estricta de responsabilidades (GUI, Control, Datos, Hardware) mediante flujo de importación unidireccional.
* [x] **Doble Vista de Usuario:** Vistas especializadas e intercambiables para el **Conductor** (tarjetas explicativas semaforizadas) y para el **Mecánico** (gráficos técnicos en tiempo real y tabla interactiva de DTCs).
* [x] **Sondeo Asíncrono en Tiempo Real:** Lectura continua mediante un hilo secundario `QThread` para mantener la interfaz gráfica fluida y reactiva.
* [x] **Soporte Híbrido de Hardware:** Compatibilidad transparente entre adaptadores físicos ELM327 USB y un emulador virtual autónomo.

### 🚀 Mejoras de Seguridad, Concurrencia y Resiliencia
* [x] **Exclusividad Serial Thread-Safe (`threading.Lock`):** Encolado seguro de órdenes críticas (`Servicio 04` — Borrado de DTCs) en `TrabajadorOBD` para que el propio hilo secundario las ejecute sin colisionar con el sondeo de sensores en el puerto USB/UART, notificando el resultado real mediante la señal `borrado_completado`.
* [x] **Cumplimiento SAE J1979 y Validación KOEO:** Verificación preventiva de motor apagado (*Key On, Engine Off*, `RPM <= 100`), advertencia modal sobre el alcance global del `Modo 04` (reinicio de monitores de emisiones y *Freeze Frame*) y re-escaneo inmediato (`Modo 03`) tras confirmar la respuesta de la ECU.
* [x] **Simulador Autónomo de 5 DTCs y Resiliencia Física:** `AdaptadorSimulador` opera sin controles extra en la GUI con 5 códigos representativos en los 3 niveles del semáforo (`P0300` y `U0100` 🔴 Alta, `P0171` y `P0420` 🟡 Media, `P0442` 🟢 Baja), físicas interrelacionadas de 10 sensores y ciclo automático de fallas:
  1. *1.er intento de conexión:* Simula cable no detectado para validar la alerta crítica inicial.
  2. *2.º intento (60 s):* Operación completa con los 5 DTCs y simulación de desconexión física en caliente al cumplirse 60 segundos.
  3. *3.er intento en adelante:* Sesión continua e ininterrumpida para demostraciones prolongadas.
* [x] **Catálogo Maestro JSON + SQLite y Decodificador SAE J2012:** Auto-construcción de la base local (`dtc_database.db`) a partir de `capa_de_datos/catalogo_dtc.json` con respaldo estructural para códigos no catalogados.
* [x] **Diseño Visual Oscuro Estandarizado (QSS) y Delegados `QListView`:** Selectores (`QComboBox`) unificados con resaltado reactivo (`#007ACC`) y buffers circulares (`deque(maxlen=100)`) en `PyQtGraph` para estabilidad de memoria RAM.
* [x] **Suite de 22 Pruebas Automatizadas (100% Passing):** Cobertura unitaria por capa e integración End-to-End (`pytest` + `pytest-qt`).

---

## 🏛 Arquitectura del Sistema (4 Capas)

El sistema sigue una regla de **importación unidireccional estricta** (de Capa 1 hacia Capa 4), evitando ciclos de dependencia:

| Capa | Nombre del Módulo | Componentes Clave | Responsabilidad Técnica |
| :--- | :--- | :--- | :--- |
| **Capa 1** | `interfaz_grafica/` | `ventana_principal.py`<br>`barra_estado.py`<br>`lista_dtc.py`<br>`dialogo_confirmacion.py`<br>`grafico_tiempo_real.py` | Presentación reactiva con PySide6. Vistas Conductor/Mecánico, tabla de DTCs, gráficos en tiempo real con `pyqtgraph`, validación KOEO y recepción asíncrona de confirmaciones de borrado. |
| **Capa 2** | `nucleo_y_controladores/` | `trabajador_obd.py`<br>`controlador_reporte.py` | Control de concurrencia. Hilo secundario `QThread` con serialización `threading.Lock` para borrado exclusivo en bus serial, emisión de señales Qt y mapeo DTO (`DTCDTO`). |
| **Capa 3** | `capa_de_datos/` | `gestor_bd.py`<br>`enriquecedor.py`<br>`cliente_rest.py`<br>`modelo_reporte.py`<br>`inicializar_db.py`<br>`catalogo_dtc.json` | Persistencia y enriquecimiento. Base de datos local SQLite (`dtc_database.db`), catálogo maestro JSON, decodificación SAE J2012 y construcción de reportes. |
| **Capa 4** | `abstraccion_de_hardware/` | `i_adaptador_obd.py`<br>`adaptador_elm327.py`<br>`adaptador_simulador.py`<br>`estrategias_protocolo.py` | Abstracción de Hardware (HAL). Interfaz abstracta ABC, driver serie real con `PySerial`, decodificador hexadecimal SAE J1979 y simulador autónomo con físicas de motor correlacionadas. |

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Interfaz Gráfica:** PySide6 (Qt6)
* **Gráficos en Tiempo Real:** PyQtGraph
* **Comunicación Serie:** PySerial (ELM327 USB / FTDI / CH340 / PL2303)
* **Base de Datos Local:** SQLite3 + Catálogo Maestro JSON
* **Pruebas Automatizadas:** PyTest & PyTest-Qt (`pytest-qt`)
* **Empaquetado Ejecutable:** PyInstaller

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio y configurar el entorno virtual
```bash
git clone https://github.com/biggerihus/blar_plus.git
cd blar_plus

# Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Otorgar permisos al puerto serie (Solo para usuarios Linux)
```bash
sudo usermod -a -G dialout $USER
```

### 3. Instalar dependencias e inicializar base de datos
```bash
pip install --upgrade pip
pip install -r requirements.txt
python3 capa_de_datos/inicializar_db.py
```

---

## 🚀 Ejecución y Compilación Portable

### Ejecución en Desarrollo
```bash
# Lanzamiento directo de la aplicación principal
python3 main.py
```

### Compilación Ejecutable Portable (PyInstaller)
Genera el ejecutable redistribuible dentro de `./dist/BlarPlus/`:

```bash
# Asegurar instalación de PyInstaller
pip install pyinstaller

# Compilar ejecutable incluyendo el catálogo maestro JSON
pyinstaller --noconfirm --onedir --windowed --name BlarPlus \
  --add-data "capa_de_datos/catalogo_dtc.json:capa_de_datos" main.py

# Probar ejecutable compilado
./dist/BlarPlus/BlarPlus
```

---

## 🧪 Suite de Pruebas Unitarias e Integración (`pytest`)

El proyecto incluye **22 pruebas integradas** que validan todas las capas del sistema, incluyendo concurrencia serial, ventanas emergentes y escenarios de fallo del simulador:

```bash
# Ejecutar la suite global en modo detallado
python3 -m pytest -v
```

### Cobertura de Pruebas:
* `tests/test_hardware.py`: Conexión, lecturas Mock, física correlacionada de 10 sensores, decodificación Hex SAE J1979 y máquina de fallas HAL. **(6/6 Passed)**
* `tests/test_datos.py`: Consultas SQLite, catálogo JSON, caché de códigos no catalogados y construcción de DTOs. **(3/3 Passed)**
* `tests/test_control.py`: Concurrencia `QThread`, serialización *thread-safe* de borrado (`Servicio 04`), emisión de señales Qt y procesamiento de DTCs. **(5/5 Passed)**
* `tests/test_gui.py`: Navegación de vistas PySide6, renderizado de tablas e interactividad de diálogos modales. **(4/4 Passed)**
* `tests/test_integracion.py`: Flujos End-to-End completos (HAL $\rightarrow$ `QThread` $\rightarrow$ GUI), alertas críticas de conexión/desconexión y borrado asíncrono. **(4/4 Passed)**

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.