"""
Modulo Adaptador ELM327
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""
# Este archivo permite que Python se comunique con un adaptador ELM327
# conectado al vehículo mediante un puerto USB. El adaptador ELM327 funciona como intermediario:
# Python -> Puerto USB -> ELM327 -> Computadora del vehículo (ECU)
# Por ejemplo:
# Python envía "010C" para solicitar las RPM del motor. --> El ELM327 transmite la solicitud al vehículo. --> El vehículo responde "41 0C 1A F8".
# La clase EstrategiasProtocolo interpreta esa información. --> Resultado: 1726 RPM.

import re
# Importamos el módulo de expresiones regulares. Permite buscar, eliminar o reemplazar caracteres dentro de un texto.
import time
# Importamos el módulo time para controlar tiempos de espera
from typing import Optional
# Optional permite indicar que una variable puede contener. un objeto de un tipo específico o el valor None.
# para que la variable puede contener: 1. Una conexión serial. 2. None, cuando todavía no existe una conexión.
import serial
# Esta biblioteca permite comunicarnos con dispositivos. conectados mediante puertos seriales, como el ELM327.
# Con serial.Serial() podemos abrir una conexión. enviar comandos y recibir respuestas.
from serial.tools import list_ports
# list_ports. Sirve para identificar los puertos seriales disponibles.
# Por ejemplo, en Linux: /dev/ttyUSB0 /dev/ttyUSB1  En Windows:COM3 COM4
from abstraccion_de_hardware.i_adaptador_obd import IAdaptadorOBD
# IAdaptadorOBD. Esta interfaz define las operaciones que debe ofrecer un adaptador OBD dentro del proyecto.

from abstraccion_de_hardware.estrategias_protocolo import EstrategiasProtocolo
# Importamos la clase que interpreta las respuestas hexadecimales.
# El adaptador ELM327 recibe la información del vehículo.
# EstrategiasProtocolo convierte esa información en datos comprensibles.
# Por ejemplo: Respuesta del vehículo: "41 0D 50"  Resultado interpretado: 80 km/h.


class AdaptadorELM327(IAdaptadorOBD):
    """Comunicación OBD-II mediante comandos AT y modos SAE J1979.
    Creamos la clase AdaptadorELM327.
    Esta clase se encarga de: Detectar puertos seriales. Conectarse al adaptador ELM327. Configurar el adaptador. Enviar comandos al vehículo.
    Recibir respuestas. Leer y borrar códigos de falla. Consultar las RPM y la velocidad.
    (IAdaptadorOBD) indica que esta clase hereda de la interfaz IAdaptadorOBD
"""
# En palabras simples: La interfaz establece las operaciones necesarias y esta clase implementa la comunicación real.

    def __init__(self, timeout: float = 2.0) -> None:
        # __init__ es el constructor de la clase.
        # Se ejecuta automáticamente cuando creamos un objeto.
        #
        # self representa el objeto que estamos creando.
        #
        # timeout: float = 2.0
        # Indica que el tiempo máximo de espera será de 2 segundos.
        #
        # float significa que acepta números decimales.
        # Por ejemplo: 1.5, 2.0 o 3.5.
        #
        # -> None indica que esta función no devuelve un valor.
        #
        # Ejemplo:
        # adaptador = AdaptadorELM327()
        #
        # Se crea un adaptador con timeout de 2 segundos.

        self.timeout = timeout
        # Guardamos el tiempo de espera dentro del objeto.
        #
        # self.timeout será utilizado posteriormente
        # cuando se abra la conexión serial.
        #
        # Ejemplo:
        # timeout = 2.0
        # self.timeout = 2.0

        self._serial: Optional[serial.Serial] = None
        # Creamos la variable que almacenará la conexión serial.
        #
        # El guion bajo en _serial indica que esta variable
        # está pensada para uso interno de la clase.
        #
        # Optional[serial.Serial] significa que puede contener
        # una conexión serial o None.
        #
        # Inicialmente vale None porque todavía no nos conectamos.
        #
        # Ejemplo:
        # Antes de conectar: self._serial = None
        # Después de conectar: contiene el objeto serial.Serial.


    @staticmethod
    # Permite utilizar la función sin crear un objeto de la clase.
    #
    # Por ejemplo:
    # AdaptadorELM327.detectar_puertos()

    def detectar_puertos() -> list[str]:
        # Función que identifica los puertos seriales disponibles.
        #
        # list[str] indica que devolverá una lista de textos.
        #
        # Por ejemplo:
        # ["/dev/ttyUSB0", "/dev/ttyUSB1"]

        return [p.device for p in list_ports.comports()]
        # list_ports.comports() obtiene los puertos detectados.
        #
        # Cada elemento p contiene información sobre un puerto.
        #
        # p.device obtiene el nombre del dispositivo.
        #
        # for p in list_ports.comports()
        # Recorre todos los puertos disponibles.
        #
        # Los corchetes [] crean una lista con sus nombres.
        #
        # Ejemplo:
        # Puerto 1: /dev/ttyUSB0
        # Puerto 2: /dev/ttyUSB1
        #
        # Resultado:
        # ["/dev/ttyUSB0", "/dev/ttyUSB1"]
        #
        # IMPORTANTE:
        # Detecta puertos seriales, no necesariamente
        # que todos sean adaptadores ELM327.


    def conectar(self, puerto: str = "/dev/ttyUSB0", baudrate: int = 38400) -> bool:
        # Función encargada de establecer la conexión con el ELM327.
        #
        # puerto: str = "/dev/ttyUSB0"
        # Indica el puerto serial que utilizaremos.
        #
        # baudrate: int = 38400
        # Indica la velocidad de comunicación serial.
        #
        # 38400 significa 38400 bits por segundo.
        # No representa la velocidad del automóvil.
        #
        # -> bool indica que la función devuelve un valor booleano.
        # En este caso devuelve True cuando logra conectarse.
        #
        # Ejemplo:
        # adaptador.conectar("/dev/ttyUSB0", 38400)

        self.desconectar()
        # Primero cerramos cualquier conexión anterior.
        #
        # ¿Por qué?
        # Para evitar mantener abierta una conexión previa
        # antes de intentar establecer una nueva.
        #
        # Si no existe conexión, desconectar() no cierra nada.

        try:
            # try permite intentar ejecutar instrucciones
            # que podrían generar un error.
            #
            # Por ejemplo:
            # El puerto no existe.
            # El dispositivo está desconectado.
            # El puerto está ocupado.
            # No tenemos permisos para utilizarlo.

            self._serial = serial.Serial(puerto, baudrate=baudrate, timeout=self.timeout,
                                        write_timeout=self.timeout)
            # Abrimos la conexión serial con el adaptador ELM327.
            #
            # serial.Serial() crea y abre la conexión.
            #
            # Parámetros:
            #
            # puerto:
            # Nombre del puerto que utilizaremos.
            # Ejemplo: "/dev/ttyUSB0".
            #
            # baudrate=baudrate:
            # Velocidad de comunicación.
            # Ejemplo: 38400 bits por segundo.
            #
            # timeout=self.timeout:
            # Tiempo máximo de espera durante una lectura.
            #
            # write_timeout=self.timeout:
            # Tiempo máximo de espera durante una escritura.
            #
            # Ejemplo:
            # serial.Serial("/dev/ttyUSB0", baudrate=38400,
            #               timeout=2.0, write_timeout=2.0)
            #
            # Si la conexión se abre correctamente,
            # queda almacenada en self._serial.

            time.sleep(0.8)
            # Detenemos la ejecución durante 0.8 segundos.
            #
            # Esto permite dar tiempo al adaptador
            # para estabilizarse después de abrir el puerto.
            #
            # 0.8 segundos = 800 milisegundos.

            self._serial.reset_input_buffer()
            # Limpiamos el búfer de entrada.
            #
            # Un búfer es una zona temporal de almacenamiento.
            #
            # El búfer de entrada puede contener mensajes
            # recibidos anteriormente.
            #
            # Por ejemplo:
            # "ELM327 v1.5"
            #
            # Al limpiarlo evitamos que esos datos anteriores
            # se mezclen con las siguientes respuestas.

            for command in ("ATZ", "ATE0", "ATL0", "ATS0", "ATH0", "ATSP0"):
                # Recorremos los comandos AT de configuración.
                #
                # Los comandos AT sirven para configurar el ELM327.
                # No son consultas de RPM, velocidad o códigos DTC.
                #
                # ATZ:
                # Reinicia el adaptador ELM327.
                #
                # ATE0:
                # Desactiva el eco de comandos.
                # Evita que el ELM327 repita el comando enviado.
                #
                # ATL0:
                # Desactiva los saltos de línea adicionales.
                #
                # ATS0:
                # Desactiva los espacios entre bytes de respuesta.
                #
                # ATH0:
                # Oculta los encabezados de las respuestas.
                #
                # ATSP0:
                # Configura la selección automática del protocolo OBD.
                #
                # El ciclo for envía estos comandos uno por uno.
                #
                # Ejemplo:
                # Primera vuelta: command = "ATZ"
                # Segunda vuelta: command = "ATE0"
                # Y así hasta "ATSP0".

                response = self._command(command)
                # Enviamos el comando actual al ELM327.
                #
                # _command() es una función de esta misma clase.
                #
                # Se encarga de:
                # Enviar el comando.
                # Esperar la respuesta.
                # Limpiar el texto recibido.
                #
                # La respuesta se almacena en response.
                #
                # Ejemplo:
                # command = "ATE0"
                # response = "ATE0 OK"

                if "?" in response:
                    # Comprobamos si la respuesta contiene "?".
                    #
                    # El ELM327 utiliza frecuentemente "?"
                    # para indicar que no reconoce un comando.
                    #
                    # Ejemplo:
                    # response = "?"
                    #
                    # La condición se cumple porque contiene "?".

                    raise RuntimeError(f"El ELM327 rechazó el comando {command}: {response}")
                    # Generamos un error indicando qué comando falló.
                    #
                    # raise sirve para lanzar una excepción.
                    #
                    # RuntimeError indica un problema durante la ejecución.
                    #
                    # La letra f permite insertar variables en el mensaje.
                    #
                    # Ejemplo:
                    # command = "ATSP0"
                    # response = "?"
                    #
                    # Mensaje:
                    # El ELM327 rechazó el comando ATSP0: ?

            return True
            # Si terminamos de configurar el adaptador
            # sin que se produzca una excepción, devolvemos True.
            #
            # True significa que el procedimiento de conexión
            # y configuración terminó correctamente.
            #
            # IMPORTANTE:
            # Esto no garantiza todavía que el vehículo responda
            # a todas las consultas OBD-II.

        except Exception:
            # Capturamos cualquier excepción producida
            # durante la conexión o configuración.
            #
            # Exception es una clase general de excepciones.
            #
            # Por ejemplo:
            # Puerto inexistente.
            # Error de comunicación.
            # Comando rechazado.

            self.desconectar()
            # Si ocurre un error, cerramos la conexión.
            #
            # Esto evita dejar abierto el puerto serial
            # después de un intento fallido.

            raise
            # Volvemos a lanzar la excepción original.
            #
            # ¿Por qué?
            # Para que la parte del programa que llamó
            # a conectar() pueda conocer el error.
            #
            # raise sin argumentos conserva la excepción actual.


    def desconectar(self) -> None:
        # Función encargada de cerrar la conexión serial.
        #
        # -> None significa que no devuelve un resultado.
        #
        # Se utiliza cuando:
        # Terminamos de usar el escáner.
        # Queremos cambiar de puerto.
        # Ocurre un error de comunicación.

        if self._serial is not None:
            # Verificamos si existe un objeto de conexión serial.
            #
            # is not None significa que la variable
            # no contiene el valor None.
            #
            # Si es None, no hay una conexión almacenada
            # que debamos cerrar.

            try:
                # Intentamos cerrar correctamente el puerto.

                if self._serial.is_open:
                    # Verificamos si el puerto está abierto.
                    #
                    # is_open es una propiedad de pyserial.
                    #
                    # True: el puerto está abierto.
                    # False: el puerto está cerrado.

                    self._serial.close()
                    # Cerramos la conexión serial.
                    #
                    # Después de esto ya no podemos enviar comandos
                    # mediante esa conexión.

            finally:
                # finally se ejecuta al salir del bloque try,
                # incluso si ocurre una excepción.
                #
                # Se utiliza para garantizar una limpieza final.

                self._serial = None
                # Eliminamos la referencia a la conexión serial.
                #
                # El objeto queda nuevamente en su estado
                # inicial respecto a esta variable.
                #
                # Ejemplo:
                # Antes: self._serial contiene una conexión.
                # Después: self._serial = None.


    def _command(self, command: str) -> str:
        # Función interna encargada de enviar comandos al ELM327.
        #
        # Recibe:
        # command: str
        # Un comando en formato de texto.
        #
        # Ejemplos:
        # "ATZ"  -> Reiniciar adaptador.
        # "03"   -> Consultar códigos DTC.
        # "04"   -> Solicitar borrado de DTC.
        # "010C" -> Consultar RPM.
        # "010D" -> Consultar velocidad.
        #
        # -> str indica que devuelve una respuesta de texto.

        if self._serial is None or not self._serial.is_open:
            # Comprobamos que exista una conexión serial abierta.
            #
            # self._serial is None:
            # No tenemos un objeto de conexión.
            #
            # or:
            # Significa "o".
            # Basta con que una condición sea verdadera.
            #
            # not self._serial.is_open:
            # Comprueba que el puerto NO esté abierto.
            #
            # Python evalúa primero la condición izquierda.
            # Si self._serial es None, no necesita consultar is_open.
            #
            # De esta forma evitamos intentar enviar un comando
            # cuando el adaptador está desconectado.

            raise RuntimeError("El adaptador ELM327 no está conectado.")
            # Generamos un error indicando que no existe
            # una conexión válida para enviar comandos.

        self._serial.reset_input_buffer()
        # Limpiamos los datos pendientes en el búfer de entrada.
        #
        # Así buscamos recibir una respuesta nueva
        # correspondiente al comando que enviaremos.
        #
        # IMPORTANTE:
        # Esto también descarta cualquier dato pendiente.

        self._serial.write((command.strip() + "\r").encode("ascii"))
        # Enviamos el comando al adaptador.
        #
        # Esta instrucción contiene varias operaciones:
        #
        # 1. command.strip()
        # Elimina espacios y saltos de línea al principio
        # y al final del comando.
        #
        # Ejemplo:
        # " 010C " -> "010C"
        #
        # 2. + "\r"
        # Agrega un retorno de carro al final.
        #
        # \r indica al ELM327 que terminó el comando.
        #
        # Ejemplo:
        # "010C" -> "010C\r"
        #
        # 3. .encode("ascii")
        # Convierte el texto a bytes usando ASCII.
        #
        # Ejemplo:
        # "010C\r" -> b"010C\r"
        #
        # 4. self._serial.write()
        # Envía esos bytes por el puerto serial.
        #
        # En resumen:
        # Preparamos el comando y lo enviamos al ELM327.

        self._serial.flush()
        # Esperamos a que los datos pendientes de salida
        # se transmitan por el puerto serial.
        #
        # Es importante distinguir:
        #
        # write():
        # Envía o coloca los datos para transmisión.
        #
        # flush():
        # Espera a que finalice la escritura pendiente.
        #
        # No significa borrar el búfer de entrada.

        raw = self._serial.read_until(b">")
        # Leemos la respuesta del ELM327.
        #
        # read_until() lee bytes hasta encontrar
        # el delimitador indicado o alcanzar el timeout.
        #
        # b">" significa que buscamos el carácter >
        # representado como un byte.
        #
        # El ELM327 utiliza normalmente > como indicador
        # de que está listo para recibir otro comando.
        #
        # Ejemplo:
        # Respuesta:
        # b"41 0C 1A F8\r\r>"
        #
        # Esta respuesta se almacena en raw.
        #
        # IMPORTANTE:
        # Si se alcanza el timeout, puede devolver
        # información incompleta sin encontrar ">".

        response = raw.decode("ascii", errors="ignore").replace(">", " ")
        # Convertimos la respuesta recibida en texto.
        #
        # 1. raw.decode("ascii", errors="ignore")
        #
        # decode("ascii"):
        # Convierte los bytes recibidos en caracteres.
        #
        # errors="ignore":
        # Ignora bytes que no se puedan interpretar
        # correctamente mediante ASCII.
        #
        # Ejemplo:
        # b"41 0C 1A F8\r>" -> "41 0C 1A F8\r>"
        #
        # 2. .replace(">", " ")
        #
        # Busca el carácter > y lo reemplaza por un espacio.
        #
        # Ejemplo:
        # "41 0C 1A F8\r>" -> "41 0C 1A F8\r "
        #
        # El resultado se guarda en response.

        response = re.sub(r"[\r\n]", " ", response)
        # Sustituimos los retornos de carro y saltos de línea.
        #
        # re.sub() busca coincidencias y las reemplaza.
        #
        # r"[\r\n]" es una expresión regular.
        #
        # \r representa un retorno de carro.
        # \n representa un salto de línea.
        #
        # Los corchetes [] indican que buscamos
        # cualquiera de esos dos caracteres.
        #
        # Ejemplo:
        # "41 0C\r\n1A F8"
        #
        # Resultado:
        # "41 0C  1A F8"
        #
        # Se reemplaza cada carácter por un espacio.

        response = re.sub(r"\s+", " ", response).strip()
        # Normalizamos los espacios de la respuesta.
        #
        # r"\s+":
        # \s identifica caracteres de espacio en blanco.
        # + significa uno o más.
        #
        # Por lo tanto, buscamos grupos de espacios
        # y los reemplazamos por un solo espacio.
        #
        # Ejemplo:
        # "41  0C   1A F8"
        #
        # Resultado:
        # "41 0C 1A F8"
        #
        # .strip():
        # Elimina espacios al principio y al final.
        #
        # Así obtenemos una respuesta más limpia.

        if not response or "UNABLE TO CONNECT" in response.upper() or "BUS INIT" in response.upper():
            # Comprobamos si la respuesta presenta problemas.
            #
            # Primera condición:
            # not response
            #
            # Es verdadera cuando response está vacío.
            #
            # Ejemplo:
            # response = ""
            #
            # Segunda condición:
            # "UNABLE TO CONNECT" in response.upper()
            #
            # Detecta un mensaje indicando que no pudo
            # establecerse comunicación con el vehículo.
            #
            # .upper() convierte el texto a mayúsculas.
            #
            # Ejemplo:
            # "Unable to connect" -> "UNABLE TO CONNECT"
            #
            # in comprueba si una cadena aparece dentro de otra.
            #
            # Tercera condición:
            # "BUS INIT" in response.upper()
            #
            # Detecta la expresión BUS INIT en la respuesta.
            #
            # El código considera cualquier respuesta que
            # contenga esa expresión como inválida.
            #
            # or significa que basta con que una condición
            # se cumpla para entrar en este bloque.

            raise RuntimeError(f"Sin respuesta válida del vehículo para {command}: {response}")
            # Lanzamos una excepción indicando:
            # El comando que enviamos.
            # La respuesta que recibimos.
            #
            # Ejemplo:
            # command = "010C"
            # response = "UNABLE TO CONNECT"
            #
            # Mensaje:
            # Sin respuesta válida del vehículo para 010C: UNABLE TO CONNECT

        return response
        # Devolvemos el texto recibido y limpiado.
        #
        # Ejemplo:
        # "41 0C 1A F8"
        #
        # Esta función todavía no calcula las RPM
        # ni interpreta los códigos de falla.
        #
        # Solamente devuelve la respuesta del ELM327.


    def leer_dtc(self) -> list[str]:
        # Función encargada de consultar los códigos de falla.
        #
        # DTC significa Diagnostic Trouble Code.
        # En español: código de diagnóstico de problemas.
        #
        # -> list[str] indica que devuelve una lista de textos.
        #
        # Ejemplo:
        # ["P0300", "P0171"]

        response = self._command("03")
        # Enviamos el comando "03" al ELM327.
        #
        # El servicio OBD-II 03 permite consultar
        # códigos de falla confirmados almacenados.
        #
        # Ejemplo de respuesta:
        # "43 02 03 00 01 71"
        #
        # 43 indica la respuesta positiva al servicio 03.
        #
        # Guardamos la información recibida en response.

        return EstrategiasProtocolo.decodificar_dtc_bytes(response)
        # Enviamos la respuesta a EstrategiasProtocolo.
        #
        # decodificar_dtc_bytes() interpreta los bytes
        # para formar los códigos DTC.
        #
        # Ejemplo:
        # Respuesta: "43 02 03 00 01 71"
        #
        # Resultado:
        # ["P0300", "P0171"]
        #
        # return devuelve la lista de códigos encontrados.
        #
        # En palabras simples:
        # El ELM327 obtiene los datos.
        # EstrategiasProtocolo interpreta los códigos.


    def limpiar_dtc(self) -> bool:
        # Función encargada de solicitar el borrado de DTC.
        #
        # -> bool significa que devuelve True o False.
        #
        # True: la respuesta contiene un indicador esperado.
        # False: no encuentra esos indicadores.
        #
        # IMPORTANTE:
        # El comando 04 puede borrar códigos de diagnóstico
        # y datos relacionados, como información congelada.
        #
        # No repara las fallas mecánicas o electrónicas
        # que originaron los códigos.

        response = self._command("04").upper()
        # Enviamos el comando "04" al adaptador.
        #
        # El servicio OBD-II 04 solicita borrar
        # información de diagnóstico relacionada con emisiones.
        #
        # _command("04"):
        # Envía el comando y recibe la respuesta.
        #
        # .upper():
        # Convierte la respuesta a mayúsculas.
        #
        # Ejemplo:
        # "ok" -> "OK"
        #
        # El resultado se almacena en response.

        return "44" in response or "OK" in response
        # Verificamos si la respuesta contiene "44" o "OK".
        #
        # "44":
        # Es el identificador de respuesta positiva al servicio 04.
        #
        # "OK":
        # Es un texto de confirmación utilizado por el ELM327
        # para determinados comandos.
        #
        # in comprueba si el texto está dentro de la respuesta.
        #
        # or significa "o".
        #
        # Ejemplo 1:
        # response = "44"
        # Resultado: True
        #
        # Ejemplo 2:
        # response = "OK"
        # Resultado: True
        #
        # Ejemplo 3:
        # response = "NO DATA"
        # Resultado: False
        #
        # IMPORTANTE:
        # El programa solamente verifica la presencia
        # de esas cadenas de texto.
        # Esto no demuestra por sí solo que todos
        # los códigos hayan desaparecido de la ECU.


    def leer_pid(self, pid: str) -> float:
        # Función encargada de consultar un PID del vehículo.
        #
        # PID significa Parameter ID.
        # Es un identificador de parámetro OBD-II.
        #
        # Cada PID permite solicitar información específica.
        #
        # Por ejemplo:
        # 010C -> Revoluciones del motor (RPM).
        # 010D -> Velocidad del vehículo.
        #
        # pid: str indica que recibimos un texto.
        #
        # -> float indica que devolveremos un número.
        #
        # Ejemplos:
        # 1726.0 RPM
        # 80.0 km/h

        pid = pid.upper().replace(" ", "")
        # Preparamos el PID antes de enviarlo.
        #
        # 1. pid.upper():
        # Convierte las letras a mayúsculas.
        #
        # Ejemplo:
        # "010c" -> "010C"
        #
        # 2. .replace(" ", ""):
        # Elimina los espacios normales del texto.
        #
        # Ejemplo:
        # "01 0C" -> "010C"
        #
        # Resultado:
        # El PID queda en un formato uniforme.
        #
        # Esto permite recibir valores como:
        # "010c", "010C" o "01 0C".

        response = self._command(pid)
        # Enviamos el PID al ELM327.
        #
        # Por ejemplo:
        # pid = "010C"
        #
        # Se envía:
        # "010C"
        #
        # El vehículo puede responder:
        # "41 0C 1A F8"
        #
        # La respuesta se guarda en response.

        if pid == "010C":
            # Comprobamos si el PID solicitado es 010C.
            #
            # == significa "es igual a".
            #
            # 01:
            # Servicio para consultar datos actuales.
            #
            # 0C:
            # Identificador de las revoluciones del motor.
            #
            # Si pid es "010C", se cumple la condición.

            return EstrategiasProtocolo.decodificar_rpm(response)
            # Enviamos la respuesta al decodificador de RPM.
            #
            # Ejemplo:
            # response = "41 0C 1A F8"
            #
            # El decodificador obtiene:
            # A = 0x1A = 26 decimal.
            # B = 0xF8 = 248 decimal.
            #
            # Fórmula SAE J1979:
            # RPM = ((A * 256) + B) / 4
            #
            # Sustituimos:
            # RPM = ((26 * 256) + 248) / 4
            # RPM = (6656 + 248) / 4
            # RPM = 6904 / 4
            # RPM = 1726
            #
            # Resultado:
            # 1726.0 RPM

        if pid == "010D":
            # Comprobamos si el PID solicitado es 010D.
            #
            # 01:
            # Servicio para consultar datos actuales.
            #
            # 0D:
            # Identificador de velocidad del vehículo.
            #
            # Si pid es "010D", se cumple la condición.

            return EstrategiasProtocolo.decodificar_velocidad(response)
            # Enviamos la respuesta al decodificador de velocidad.
            #
            # Ejemplo:
            # response = "41 0D 50"
            #
            # El byte correspondiente a la velocidad es:
            # 50 hexadecimal = 80 decimal.
            #
            # Fórmula SAE J1979:
            # Velocidad = A
            #
            # Resultado:
            # 80.0 km/h
            #
            # En este caso no necesitamos combinar dos bytes.
            # La velocidad utiliza un solo byte de datos.

        raise ValueError(f"PID no soportado: {pid}")
        # Si el PID no coincide con "010C" ni con "010D",
        # generamos una excepción.
        #
        # ValueError indica que el valor proporcionado
        # no es válido para esta operación.
        #
        # Ejemplo:
        # pid = "0105"
        #
        # Mensaje:
        # PID no soportado: 0105
        #
        # IMPORTANTE:
        # Esta función solamente tiene implementados
        # los decodificadores para RPM y velocidad.
        #
        # Aunque otros PID existan en OBD-II,
        # esta función no los interpreta.
