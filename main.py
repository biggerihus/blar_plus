"""
Punto de entrada principal del sistema Blar Plus.

Inicializa el motor de PySide6 y despliega la ventana principal.

Autor: Equipo Blar Plus
"""

import sys
from PySide6.QtWidgets import QApplication
from interfaz_grafica.ventana_principal import VentanaPrincipal


def main() -> None:
    # 1. Crear el ciclo de eventos de la aplicación Qt
    app = QApplication(sys.argv)

    # 2. Instanciar y mostrar la ventana principal
    ventana = VentanaPrincipal()
    ventana.show()

    # 3. Mantener la aplicación en ejecución
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
