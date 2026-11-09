"""
Punto de Entrada Principal e Integrador del Sistema Blar Plus.

Este módulo se encarga de instanciar e interconectar todas las capas de la arquitectura:
- Capa de Abstracción de Hardware (Adaptador OBD / Simulador).
- Capa Núcleo y Concurrencia (Hilo secundario de sondeo en segundo plano).
- Capa de Interfaz Gráfica (Ventana Principal PySide6).

Autor: Equipo Blar Plus
"""

# Importación del módulo de sistema para manejo de argumentos de consola y salida del proceso
import sys

# Importación de la clase principal de PySide6 para la gestión del bucle de eventos Qt
from PySide6.QtWidgets import QApplication

# Importación del adaptador de hardware en modo simulador para lectura de la ECU
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador

# Importación de la clase del hilo secundario encargado del sondeo asíncrono a 10 Hz
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD

# Importación de la ventana principal de la interfaz gráfica de usuario
from interfaz_grafica.ventana_principal import VentanaPrincipal


def main() -> None:
    # Instanciar la aplicación Qt encargada de administrar el ciclo de vida y eventos
    app = QApplication(sys.argv)

    # Inicializar la capa de hardware (Simulador del bus de datos OBD-II)
    adaptador_hardware = AdaptadorSimulador()

    # Instanciar el contenedor de la interfaz gráfica principal (VentanaPrincipal)
    ventana_principal = VentanaPrincipal()

    # Instanciar el hilo secundario (QThread), inyectándole el adaptador de hardware
    trabajador_obd = TrabajadorOBD(adaptador=adaptador_hardware)

    # Conectar la señal de transmisión de DTCs del hilo con el slot de recepción de la GUI
    # Cada vez que 'trabajador_obd' lee datos a 10 Hz, transfiere la lista de cadenas a la ventana
    trabajador_obd.datos_recibidos.connect(ventana_principal.recibir_dtcs_asincronos)

    # Conectar la señal de errores del hilo con la barra de estado visual (LED) de la GUI
    # Si ocurre una desconexión o fallo, actualiza el indicador visual y muestra el mensaje
    trabajador_obd.error_ocurrido.connect(
        lambda mensaje_error: ventana_principal.barra_estado_widget.actualizar_estado(
            conectado=False, mensaje=mensaje_error
        )
    )

    # Arrancar la ejecución en segundo plano del hilo asíncrono de sondeo (ejecuta trabajador.run())
    trabajador_obd.start()

    # Renderizar y mostrar en pantalla la ventana principal con todos sus paneles e indicadores
    ventana_principal.show()

    # Garantizar la detención limpia del hilo secundario al cerrar la ventana principal
    # La señal 'aboutToQuit' ejecuta el método .detener() para liberar puertos y detener bucles
    app.aboutToQuit.connect(trabajador_obd.detener)

    # Iniciar el bucle de eventos principal de Qt y retornar el código de salida al terminar
    sys.exit(app.exec())


if __name__ == "__main__":
    # Punto de ejecución al invocar directamente el script desde la línea de comandos
    main()
