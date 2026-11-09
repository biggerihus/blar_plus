"""
Punto de Entrada Principal e Integrador del Sistema Blar Plus.

Este módulo se encarga de instanciar e interconectar todas las capas de la arquitectura:
- Capa de Abstracción de Hardware (Adaptador OBD / Simulador).
- Capa Núcleo y Concurrencia (Hilo secundario de sondeo en segundo plano).
- Capa de Interfaz Gráfica (Ventana Principal PySide6).

Soporta selección de modo (Simulador vs ELM327 Real) mediante argumentos de consola.

Autor: Equipo Blar Plus
"""

# Importación del módulo argparse para procesar argumentos de línea de comandos
import argparse
# Importación del módulo de sistema para argumentos y salida del proceso
import sys

# Importación de la clase principal de PySide6 para la gestión del bucle de eventos Qt
from PySide6.QtWidgets import QApplication

# Importación de los adaptadores de hardware (Simulador y ELM327 Real)
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador
from abstraccion_de_hardware.adaptador_elm327 import AdaptadorELM327

# Importación de la clase del hilo secundario encargado del sondeo asíncrono a 10 Hz
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD

# Importación de la ventana principal de la interfaz gráfica de usuario
from interfaz_grafica.ventana_principal import VentanaPrincipal


def main() -> None:
    # Configuración del parseador de argumentos por línea de comandos
    parser = argparse.ArgumentParser(description="Escáner Automotriz Blar Plus")
    # Argumento para seleccionar el modo de operación del escáner
    parser.add_argument(
        "--modo",
        choices=["simulador", "real"],
        default="simulador",
        help="Modo de operación del hardware: 'simulador' (por defecto) o 'real'",
    )
    # Argumento para definir el puerto serie del dispositivo físico
    parser.add_argument(
        "--puerto",
        default="/dev/ttyUSB0",
        help="Puerto USB/Serie para el escáner ELM327 (por defecto: /dev/ttyUSB0)",
    )
    # Procesamiento de los argumentos ingresados en consola
    args = parser.parse_args()

    # Instanciar la aplicación Qt encargada de administrar el ciclo de vida y eventos
    app = QApplication(sys.argv)

    # Selección e instanciación del adaptador de hardware según los argumentos
    if args.modo == "real":
        print(f"[!] Iniciando escáner en MODO REAL conectando a {args.puerto}...")
        adaptador_hardware = AdaptadorELM327()
    else:
        print("[+] Iniciando escáner en MODO SIMULADOR...")
        adaptador_hardware = AdaptadorSimulador()

    # Instanciar el contenedor de la interfaz gráfica principal
    ventana_principal = VentanaPrincipal()

    # Instanciar el hilo secundario (QThread), inyectándole el adaptador de hardware seleccionado
    trabajador_obd = TrabajadorOBD(adaptador=adaptador_hardware)

    # Conectar la señal de transmisión de DTCs del hilo con el slot de recepción de la GUI
    trabajador_obd.datos_recibidos.connect(ventana_principal.recibir_dtcs_asincronos)

    # Conectar la señal de errores del hilo con la barra de estado visual (LED) de la GUI
    trabajador_obd.error_ocurrido.connect(
        lambda mensaje_error: ventana_principal.barra_estado_widget.actualizar_estado(
            conectado=False, mensaje=mensaje_error
        )
    )

    # Arrancar la ejecución en segundo plano del hilo asíncrono de sondeo
    trabajador_obd.start()

    # Renderizar y mostrar en pantalla la ventana principal
    ventana_principal.show()

    # Garantizar la detención limpia del hilo secundario al cerrar la ventana principal
    app.aboutToQuit.connect(trabajador_obd.detener)

    # Iniciar el bucle de eventos principal de Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
