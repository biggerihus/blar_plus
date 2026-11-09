"""
 Punto de entrada y cableado General: Blar Plus
 Integra Adaptador de Hardware, capa de datos , controlador y GUI Qt
 Sprint 3
 """
from interfaz_grafica.dialogo_confirmacion import DialogoConfirmacion
import sys
from PySide6.QtWidgets import QApplication, QDialog 

# Capa de Abstracción de Hardware
from abstraccion_de_hardware.adaptador_simulador import AdaptadorSimulador

# Capa de Control y Concurrencia
from nucleo_y_controladores.trabajador_obd import TrabajadorOBD

# Capa de Interfaz Gráfica
from interfaz_grafica.ventana_principal import VentanaPrincipal
def main() -> None:
    #Instanciamos el ciclo de eventos QT
    app = QApplication(sys.argv)

    #Enlazamos la accion de norrado de la GUI con la memoria del adaptador

    adaptador = AdaptadorSimulador()

    #Enelazamos la accion del boton borrar de la GUI con la memoria del adaptador
    def abrir_dialogo_borrado_sincronizado(self: VentanaPrincipal):
        dialogo = DialogoConfirmacion(self)
        resultado = dialogo.exec()

        if resultado == QDialog.DialogCode.Accepted:
            # Limpiamos  la memoria del adaptador/vehículo
            adaptador.limpiar_dtc()
            # Limpiamos visualmente la tabla
            self.lista_dtc_widget.cargar_reportes([])
            self.barra_estado_widget.actualizar_estado(
                True, "Códigos DTC borrados de la memoria con éxito."
            )
        else:
            self.barra_estado_widget.actualizar_estado(
                True, "Operación de borrado cancelada."
            )
    # Conectar el método sincronizado a la clase VentanaPrincipal
    VentanaPrincipal.abrir_dialogo_borrado = abrir_dialogo_borrado_sincronizado

    # Instancioamos la Ventana Principal
    ventana = VentanaPrincipal()
    

    #Instanciamos Hilo de Fondo con el adaptador
    trabajador = TrabajadorOBD(adaptador)

    #Conectamos los datos leídos con la tabla DTC de la GUI
    trabajador.datos_recibidos.connect(ventana.recibir_dtcs_asincronos)

    #Conectar errores de comunicación a la barra de estado

    def manejar_error(mensaje: str) -> None:
         ventana.barra_estado_widget.actualizar_estado(False, mensaje)

    trabajador.error_ocurrido.connect(manejar_error)

    #Iniciamos Hilo en segundo plano y mostrar Ventan Principal

    trabajador.start()
    ventana.barra_estado_widget.actualizar_estado(True, "Adaptador Conetado y Sondeo Activo")
    ventana.show()

    #Limpiamos el Hilo al cerrar la Ventana

    codigo_salida = app.exec()
    trabajador.detener()
    sys.exit(codigo_salida)

if __name__ == "__main__":
    main()


