"""
Decodificadores de respuestas OBD-II conforme a SAE J1979.
Autor: Mendivil Jimenez Jose Luis
Capa: Abstraccion de Hardware (HAL) / Capa 4
"""
# Decodificadores de respuestas OBD-II conforme a SAE J1979. (SAE J1979: estándar que define servicios de diagnóstico OBD.)
# Su función es recibir información hexadecimal que envía el escáner ELM327 y convertirla en información que Python pueda entender.
# por ejemplo 
# Información que recibe del vehículo -> 41 0C 1A F8 -- Respuesta hexadecimal del PID de RPM
#  41  0C  1A  F8
#  │   │   │   └── Byte B (Segundo byte de datos)
#  │   │   └────── Byte A (Primer byte de datos)
#  │   └────────── PID consultado (0C = RPM)
#  └────────────── Respuesta válida a Modo 01 (0x01 + 0x40 = 0x41)
# El decodificador procesa los bytes --> --> 
# Resultado en Python para entenderla --> 1726 RPM


""" en palabras simples:
con Svierte información recibida en datos comprensibles .
"""

import re # Significa Regular Expressions o expresiones regulares. Para buscar y reconocer patrones dentro de un texto.
# Por ejemplo, si recibimos: "41 0C 1A F8" Podemos identificar cada pareja de caracteres hexadecimales.

class EstrategiasProtocolo:
    """ esta clase agrupa todas las funciones encargadas de interpretar las respuestas del vehículo.
        Por ejemplo:
        - Interpretar RPM.
        - Interpretar velocidad.
        - Interpretar códigos DTC.
        """


    @staticmethod  #para poder utilizar esta función sin crear un objeto de la clase.
    def _bytes(hex_str: str) -> list[int]:
    # funcion que resive un string hexadecimal y lo convierte en una lista de enteros.
        """ Por ejemplo, si recibimos: EstrategiasProtocolo._bytes("41 0C 1A F8") """

        cleaned = re.sub(r"(?i)\b(?:SEARCHING|CAN|ISO|STOPPED)\b", " ", hex_str) 
            # -- Mensajes de Estado del Chip ELM327 -- 
            # SEARCHING...: Aparece cuando el chip está buscando automáticamente qué protocolo de comunicación utiliza el vehículo.
            # CAN ERROR: Aparece cuando el chip no puede comunicarse con el vehículo a través del protocolo CAN.
            # ISO ERROR: Aparece cuando el chip no puede comunicarse con el vehículo a través del protocolo ISO.
            # STOPPED: Aparece cuando el chip ha detenido la comunicación con el vehículo debido a un error o a una desconexión.
        # re.sub() sirve para buscar un patrón y reemplazarlo por otro texto. En este caso busca palabras que puede entregar en el ELM327 SEARCHING ,CAN, ISO, STOPPED
        # Y las reemplaza por un espacio.

        tokens = re.findall(r"(?i)[0-9a-f]{2}", cleaned)
        # re.findall() busca todas las coincidencias de un patrón en un texto y devuelve una lista con ellas.
        # En este caso busca exactamente dos caracteres hexadecimales (0-9, a-f) en el texto limpio y las guarda en la lista tokens.

        residue = re.sub(r"(?i)[0-9a-f]{2}|[\s>]", "", cleaned)
        # comprueba si quedo algun caracter extraño despues de reconocer los tokens hexadecimales. Si queda algo que no sea un token hexadecimal, un espacio o el símbolo ">", se considera un residuo.
        # y los reem plaza por un string vacio.

        if not tokens or residue:
        # Si no encontramos bytes (not tokens) o quedó algún carácter extraño (residue)
            raise ValueError(f"Trama hexadecimal inválida: {hex_str!r}")
            # si se cumple alguna de estas condiciones, se lanza un error indicando que la trama hexadecimal es inválida.
        return [int(token, 16) for token in tokens]
    
        # Convierte cada token hexadecimal en un entero decimal utilizando base 16.y devuelve la lista de enteros.
        """ 
        Convierte cada número hexadecimal a decimal.
        Hexadecimal     Decimal
        41	            65
        0C	            12
        1A	            26
        F8	            248
        Resultado: [65, 12, 26, 248]
        """

    @staticmethod
    def decodificar_rpm(hex_str: str) -> float:
        # funcion para interpretar las RPM (Revoluciones Por Minuto) del motor a partir de la respuesta hexadecimal del vehículo.
        data = EstrategiasProtocolo._bytes(hex_str)
        # el objetivo es convertir la informacion hexadecimal en una lista de bytes de nombre data
        try:
            i = next(i for i in range(len(data) - 3) if data[i:i + 2] == [0x41, 0x0C])
                # 0x41: respuesta positiva del modo 01.
                # 0x0C: identificador PID de RPM.
                # buscamos esa combinación para encontrar dónde comienza la respuesta
            # len(data) obtiene la cantidad de elementos de la lista.
            # range(len(data) - 3) genera las posiciones donde puede comenzar una respuesta de RPM.
            # [0x41, 0x0C] es la combinación de bytes que indica que la respuesta contiene información de RPM.
            # next() devuelve el primer índice i donde se encuentra la combinación de bytes [0x41, 0x0C].
            """ en el ejemplo de respuesta 41 0C 1A F8, la combinación [0x41, 0x0C] se encuentra en las posiciones 0 y 1, por lo que i será igual a 0. """
            a, b = data[i + 2:i + 4]
            # Aquí extraemos los dos bytes que contienen el valor de RPM.
            """ 41 0C 1A F8 -->  a = 1A hexadecimal = 26 decimal.  b = F8 hexadecimal = 248 decimal. """


        except (StopIteration, ValueError):
            # si ocurre alguno de esos errores durante la búsqueda, ejecutaremos una alternativa.
            if len(data) == 2: # Comprueba si solamente recibimos dos bytes.
                a, b = data  #Esto permite aceptar una trama que ya contiene únicamente los valores a y b.
            else:
                raise ValueError(f"Trama RPM inválida: {hex_str!r}")
        return ((a * 256) + b) / 4.0
        # Fórmula Estándar de RPM (SAE J1979)
        """ (a * 256) + b) / 4.0 -->  (26 * 256) + 248) / 4.0 = (6656 + 248) / 4.0 = 2904.0/4 = 1726.0 RPM """
    



    @staticmethod
    def decodificar_velocidad(hex_str: str) -> float:
    # funcion para interpretar la velocidad del vehículo a partir de la respuesta hexadecimal del vehículo. 
        data = EstrategiasProtocolo._bytes(hex_str)
        # convierte la trama hexadecimal a bytes.
        """ ejemplo "41 0D 50" --> [65, 13, 80] """
        try:
            i = next(i for i in range(len(data) - 2) if data[i:i + 2] == [0x41, 0x0D])
            # Intenta encontrar la respuesta correspondiente al PID de velocidad.
            # 0x41 : respuesta positiva del modo 01.
            # 0x0D : identificador PID de velocidad.
            
            return float(data[i + 2])
            #Extrae el byte correspondiente a la velocidad y lo convierte en decimal.
            """ En nuestro ejemplo: 50 hexadecimal = 80 decimal, por lo que la velocidad es 80 km/h. """

        except StopIteration:
            if len(data) == 1:
                # Si no encuentra la combinación anterior, intenta interpretar una trama que contenga solamente un byte.
                return float(data[0])
                # Si existe un solo byte, lo devuelve como número decimal.
            raise ValueError(f"Trama de velocidad inválida: {hex_str!r}")
            # no se pudo interpretar la trama, por lo que se lanza un error.


    @staticmethod
    def decodificar_dtc_bytes(hex_str: str) -> list[str]:
        # función que permite interpretar los códigos de falla del automóvil.
        # recibe hexadecimal y devuelve una lista de cadenas de texto.
        data = EstrategiasProtocolo._bytes(hex_str)
        # Convertimos la trama a bytes.
        """ por ejemplo "43 02 03 00 01 71" --> [67, 2, 3, 0, 1, 113]"""
        try:
            start = data.index(0x43) + 1
            # El byte 43 representa la respuesta positiva al servicio OBD-II de lectura de DTC (modo 03).
            # data.index(0x43) buscamos donde aparece el byte 43. + 1 comenzaremos después de ese encabezado.
            data = data[start:]
            # data[start:] conserva los elementos desde esa posición hasta el final.
        except ValueError:
            # data[start:] conserva los elementos desde esa posición hasta el final.
            pass # no hacer nada


        # Algunas interfaces incluyen un byte inicial con el número de DTC.
        # Se reconoce solo cuando la longitud restante es impar y el contador
        # coincide exactamente con los pares de bytes que siguen.

        
        if len(data) % 2 == 1 and data and data[0] == (len(data) - 1) // 2:
            data = data[1:]

                # len(data) % 2 == 1: comprueba si la cantidad de bytes es impar.
                # data: comprueba que la lista no esté vacía.
                # data[0]: obtiene el primer byte.
                # (len(data) - 1) // 2: calcula cuántos pares de bytes hay después del primero.
        result = []
        # Creamos una lista vacía donde guardaremos los códigos DTC ya interpretados.
        families = "PCBU"
        # Esta cadena contiene las cuatro familias de códigos OBD-II: 
        # Posición	Letra	Categoría
        # 0	        P	    Powertrain (tren motriz)
        # 1	        C	    Chassis (chasis)
        # 2	        B	    Body (carrocería)
        # 3	        U	    Network (red de comunicación)


        for i in range(0, len(data) - 1, 2):
            # recorre la lista de dos en dos. Porque cada código DTC se representa mediante dos bytes.
            a, b = data[i], data[i + 1]
            # Extraer cada pareja de bytes que representan un código DTC.
            if a == 0 and b == 0:
                continue
            # Si los dos bytes son cero, no representan un código de falla. continue hace que el ciclo pase a la siguiente pareja.
            family = families[(a >> 6) & 0x03]
            # ***aquí comienza la interpretación real del código.
            # a >> 6 Se desplazan 6 bits hacia la derecha porque los primeros 2 bits de un código DTC indican a qué familia pertenece la falla
            #  & 0x03  conserva únicamente los dos bits menos significativos del resultado. Esto permite obtener un número entre 0 y 3.
            # Luego, se utiliza ese número como índice para seleccionar la letra correspondiente de la cadena families.
            # 0 = P.  1 = C.  2 = B.  3 = U.
            digit = (a >> 4) & 0x03
            # Desplaza los bits cuatro posiciones hacia la derecha y conserva los dos bits necesarios. Así obtenemos el primer dígito del código DTC.
            result.append(f"{family}{digit}{a & 0x0F:X}{b:02X}")
            # Esto reúne toda la información para formar el código.
            # family: familia del código.
            # digit: primer dígito.
            # a & 0x0F: tercer carácter hexadecimal.
            # :X: convierte el valor a hexadecimal en mayúsculas.
            #b:02X: convierte el segundo byte a dos caracteres hexadecimales.
            # por ejemplo, si a = 0x03 y b = 0x00, el código DTC sería "P0300".
        return result
    # y Devuelve la lista de códigos de falla encontrados.
