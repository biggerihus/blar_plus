"""
Punto de Entrada Principal del Sistema de Monitoreo Vehicular Blar Plus.

Orquesta la inicialización de la aplicación Qt, detecta el hardware disponible
(adaptador físico ELM327 USB o Modo Simulador), enlaza las señales asíncronas
entre Capa 2 (`TrabajadorOBD`) y Capa 1 (`VentanaPrincipal`) y garantiza el
cierre limpio del hilo secundario al finalizar la ejecución.

Autor: Equipo BLAR (UACM)
Capa: Orquestación / Punto de Entrada
"""

# Importación del módulo sys para gestión de argumentos CLI y código de salida
import sys
# Importación de QApplication para el bucle principal de eventos gráficos Qt6
from PySide6.QtWidgets import QApplication

# Importación de los adaptadores concretos de Capa 4 (HAL)
from abstraccion_de_hardware.adaptador_elm327 import AdaptadorELM327
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
# Importación de la ventana principal de Capa 1 (GUI)
from interfaz_grafica.ventana_principal import VentanaPrincipal
# Importación del gestor de concurrencia de Capa 2 (Núcleo)
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD


def main() -> None:
    """Inicializa la interfaz gráfica, configura el hilo OBD-II y ejecuta la aplicación."""
    app = QApplication(sys.argv)

    # Instanciación de la ventana principal (inicializa internamente ControladorReporte y SQLite)
    ventana_principal = VentanaPrincipal()

    # Detección de hardware inicial según argumentos CLI o puertos serie disponibles
    puertos_detectados = AdaptadorELM327.detectar_puertos()
    forzar_simulador = "--simulador" in sys.argv

    if forzar_simulador or not puertos_detectados:
        print("[!] Iniciando escáner en MODO SIMULADOR...")
        adaptador_inicial = AdaptadorSimulador()
        ventana_principal._adaptador_simulador = adaptador_inicial
    else:
        print(f"[!] Iniciando escáner en MODO REAL conectando a {puertos_detectados[0]}...")
        adaptador_inicial = AdaptadorELM327()

    # Instanciación única del hilo trabajador OBD-II (Capa 2)
    trabajador_obd = TrabajadorOBD(adaptador=adaptador_inicial)

    # Enlace de señales Qt entre TrabajadorOBD (Capa 2) y VentanaPrincipal (Capa 1)
    ventana_principal.set_trabajador_obd(trabajador_obd)
    trabajador_obd.datos_recibidos.connect(ventana_principal.recibir_dtcs_asincronos)
    trabajador_obd.sensores_recibidos.connect(ventana_principal.recibir_sensores_asincronos)

    # Arrancar el hilo secundario en estado de espera (sin sondear hasta pulsar Conectar)
    trabajador_obd.start()

    # Mostrar interfaz gráfica y ejecutar bucle principal
    ventana_principal.show()
    codigo_salida: int = app.exec()

    # Cierre seguro y ordenado del hilo secundario y del puerto serial antes de salir
    trabajador_obd.detener()
    sys.exit(codigo_salida)


if __name__ == "__main__":
    main()
