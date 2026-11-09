# 🚗 Escáner Automotriz Blar Plus

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-green?logo=qt&logoColor=white)
![PyQtGraph](https://img.shields.io/badge/Plotting-PyQtGraph-orange)
![SQLite](https://img.shields.io/badge/Database-SQLite3-blueviolet?logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passed-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

Sistema profesional de diagnóstico automotriz OBD-II desarrollado en Python 3.10+ y PySide6. Implementa una **arquitectura desacoplada de 4 capas** con muestreo en tiempo real a 10 Hz mediante comunicación serie (dispositivos USB ELM327) o emulación simulada con física vehicular correlacionada y pruebas de resiliencia ante fallos físicos de hardware. Desarrollado bajo la metodología **Scrumban**.

---

## 👥 Equipo de Desarrollo ("BLAR")

| Desarrollador | Rol / Capa Asignada | Módulo Principal |
| :--- | :--- | :--- |
| **Mendivil Jiménez José Luis** | Capa 4 — Abstracción de Hardware (HAL) | `abstraccion_de_hardware/` |
| **Chavarría Mendoza Antonio** | Capa 3 — Persistencia y Datos | `capa_de_datos/` |
| **Polanco Romero Erick** | Capa 2 — Núcleo y Concurrencia | `nucleo_y_controladores/` |
| **Estrada Loaiza Rogelio** | Capa 1 — Interfaz Gráfica (GUI) | `interfaz_grafica/` |

---

## 🎯 Objetivos Planeados vs. Mejoras Recientes

### 📌 Objetivos Planeados Iniciales
* [x] **Arquitectura Multicapa:** Separación estricta de responsabilidades (GUI, Control, Datos, Hardware) mediante flujo de importación unidireccional.
* [x] **Doble Vista de Usuario:** Vistas especializadas e intercambiables para el **Conductor** (tarjetas explicativas semaforizadas) y para el **Mecánico** (gráficos técnicos en tiempo real y tabla interactiva de DTCs).
* [x] **Sondeo Asíncrono en Tiempo Real:** Lectura continua a 10 Hz mediante un hilo secundario `QThread` para mantener la interfaz fluida.
* [x] **Soporte Híbrido de Hardware:** Compatibilidad transparente entre adaptadores físicos ELM327 USB y un emulador virtual.

### 🚀 Mejoras Visuales, de Estabilidad y Resiliencia Implementadas
* [x] **Diseño Visual Oscuro Estandarizado (QSS):** Unificación de todos los selectores (`QComboBox`) con fondo `#1E1E1E`, contornos curvos reactivos (azul `#007ACC` al posar el cursor/hover) y flecha descendente (▼).
* [x] **Integración de Delegados `QListView`:** Asignación explícita de `.setView(QListView())` en los menús desplegables para forzar el resaltado en azul puro con letras blancas en negrita durante la selección de elementos en entornos Linux/Windows.
* [x] **Simulador de Resiliencia ante Fallas Físicas:** Máquina de estados integrada en `AdaptadorSimulador` que valida:
  1. *Fallo de conexión en el 1.er intento:* Simulación de cable no detectado para verificar la reacción de la GUI.
  2. *Desconexión física en caliente a los 40 s:* Simulación de la desconexión del cable durante el monitoreo para probar la recuperación del sistema.
* [x] **Optimización de Memoria RAM (`deque`):** Uso de buffers circulares de tamaño fijo (`maxlen=100`) en el gráfico técnico para evitar fugas de memoria en sesiones prolongadas.
* [x] **Alertas Modales Limpias y Formateadas:** Visualización en texto plano con medición exacta de duración de sesión (ej. *"Pérdida de comunicación tras 40 s de sesión activa"*).
* [x] **Suite de 18 Pruebas Automatizadas (100% Passing):** Suite completa con `pytest` que abarca pruebas unitarias por capa e integración End-to-End (`test_integracion.py`).
* [x] **Empaquetado Portable Oficial (`BlarPlus.spec`):** Configuración lista para compilar ejecutables portables mediante PyInstaller.

---

## 🏛 Arquitectura del Sistema (4 Capas)

El sistema sigue una regla de **importación unidireccional estricta** (de Capa 1 hacia Capa 4), evitando ciclos de dependencia:

| Capa | Nombre del Módulo | Componentes Clave | Responsabilidad Técnica |
| :--- | :--- | :--- | :--- |
| **Capa 1** | `interfaz_grafica/` | `ventana_principal.py`<br>`barra_estado.py`<br>`lista_dtc.py`<br>`dialogo_confirmacion.py`<br>`grafico_tiempo_real.py` | Presentación reactiva con PySide6. Vistas alternativas (Conductor/Mecánico), tabla interactiva de DTCs, gráficos a alta frecuencia con pyqtgraph y selectores estandarizados. |
| **Capa 2** | `nucleo_y_controladores/` | `trabajador_obd.py`<br>`controlador_reporte.py` | Control de concurrencia. Hilo secundario `QThread` para sondeos a 10 Hz sin congelar la GUI, emisión de señales Qt y mapeo DTO (`DTCDTO`). |
| **Capa 3** | `capa_de_datos/` | `gestor_bd.py`<br>`enriquecedor.py`<br>`cliente_rest.py`<br>`modelo_reporte.py`<br>`inicializar_db.py` | Persistencia y enriquecimiento. Consultas a SQLite (`dtc_database.db`), integración con API REST HTTP para diagramas y construcción de reportes. |
| **Capa 4** | `abstraccion_de_hardware/` | `i_adaptador_obd.py`<br>`adaptador_elm327.py`<br>`adaptador_simulador.py`<br>`estrategias_protocolo.py` | Abstracción de Hardware (HAL). Interfaz abstracta ABC, driver serie real con `PySerial`, decodificador SAE J1979 y simulador con física de motor correlacionada. |

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Interfaz Gráfica:** PySide6 (Qt6)
* **Gráficos en Tiempo Real:** PyQtGraph
* **Comunicación Serie:** PySerial (ELM327 USB / FTDI / CH340 / PL2303)
* **Base de Datos Local:** SQLite3
* **Pruebas Automatizadas:** PyTest & PyTest-Qt (`pytest-qt`)
* **Empaquetado Executable:** PyInstaller

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio y configurar el entorno virtual
```bash
git clone https://github.com/biggerihus/blar_plus.git
cd blar_plus

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate
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

### ⚙️ Modos de Operación del Simulador
El simulador cuenta con la bandera `modo_secuencia_fallos` en `AdaptadorSimulador`:
* **Modo Pruebas de Resiliencia (`modo_secuencia_fallos = True`):** Evalúa la respuesta de la GUI ante un fallo en el primer intento de conexión y una desconexión en caliente a los 40 segundos.
* **Modo Demostración Continua (`modo_secuencia_fallos = False`):** Permite un monitoreo ilimitado y sin interrupciones para presentaciones o pruebas continuas de interfaz.

### Compilación Ejecutable Portable (PyInstaller)
Genera el ejecutable redistribuible dentro de `./dist/BlarPlus/`:

```bash
# Asegurar instalación de PyInstaller
pip install pyinstaller

# Compilar ejecutable con el archivo .spec configurado
pyinstaller --noconfirm BlarPlus.spec

# Probar ejecutable compilado
./dist/BlarPlus/BlarPlus
```

---

## 🧪 Suite de Pruebas Unitarias e Integración (`pytest`)

El proyecto incluye 18 pruebas integradas que validan todas las capas del sistema:

```bash
# Ejecutar la suite global en modo detallado
python3 -m pytest -v
```

### Cobertura de Pruebas:
* `tests/test_hardware.py`: Conexión, lecturas Mock, física correlacionada, decodificación Hex SAE J1979 y máquina de fallas HAL. **(6/6 Passed)**
* `tests/test_datos.py`: Consultas SQLite, tolerancia a fallos de red y construcción de DTOs. **(3/3 Passed)**
* `tests/test_control.py`: Concurrencia a 10 Hz (`QThread`), emisión de señales Qt y procesamiento de DTCs. **(4/4 Passed)**
* `tests/test_gui.py`: Navegación de vistas PySide6, renderizado de tablas e interactividad modal. **(4/4 Passed)**
* `tests/test_integracion.py`: Flujo End-to-End completo (HAL $\rightarrow$ `QThread` $\rightarrow$ GUI). **(1/1 Passed)**

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**.