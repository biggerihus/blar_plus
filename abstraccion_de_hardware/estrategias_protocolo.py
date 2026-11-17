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

import re  # Significa Regular Expressions o expresiones regulares. Para buscar y reconocer patrones dentro de un texto.


class EstrategiasProtocolo:
    """
    Esta clase agrupa todas las funciones encargadas de interpretar las respuestas del vehículo:
    - Interpretar RPM, velocidad y 8 sensores adicionales del Modo 01 SAE J1979.
    - Interpretar códigos DTC del Modo 03.
    """

    @staticmethod  # Para poder utilizar esta función sin crear un objeto de la clase.
    def _bytes(hex_str: str) -> list[int]:
        """Recibe un string hexadecimal y lo convierte en una lista de enteros."""
        cleaned = re.sub(r"(?i)\b(?:SEARCHING|CAN|ISO|STOPPED)\b", " ", hex_str)
        # Reemplaza mensajes de estado transitorios del chip ELM327 por espacios.

        tokens = re.findall(r"(?i)[0-9a-f]{2}", cleaned)
        # Busca parejas de caracteres hexadecimales (bytes) en el texto limpio.

        residue = re.sub(r"(?i)[0-9a-f]{2}|[\s>]", "", cleaned)
        # Comprueba si quedó algún carácter extraño tras extraer los bytes hexadecimales.

        if not tokens or residue:
            raise ValueError(f"Trama hexadecimal inválida: {hex_str!r}")

        return [int(token, 16) for token in tokens]

    @staticmethod
    def _extraer_bytes_pid(hex_str: str, pid_byte: int, cantidad_bytes: int) -> list[int]:
        """
        Localiza la cabecera positiva [0x41, pid_byte] dentro de la trama y extrae
        la cantidad exacta de bytes de datos solicitada por el estándar SAE J1979.
        """
        data = EstrategiasProtocolo._bytes(hex_str)
        try:
            i = next(
                idx
                for idx in range(len(data) - (1 + cantidad_bytes))
                if data[idx : idx + 2] == [0x41, pid_byte]
            )
            return data[i + 2 : i + 2 + cantidad_bytes]
        except StopIteration:
            # Permite aceptar tramas crudas que contengan únicamente los bytes de datos
            if len(data) == cantidad_bytes:
                return data
            raise ValueError(f"Trama inválida para PID 0x{pid_byte:02X}: {hex_str!r}")

    @staticmethod
    def decodificar_rpm(hex_str: str) -> float:
        """Interpreta las RPM del motor (PID 010C). Fórmula: ((A * 256) + B) / 4."""
        a, b = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x0C, 2)
        return ((a * 256) + b) / 4.0

    @staticmethod
    def decodificar_velocidad(hex_str: str) -> float:
        """Interpreta la velocidad del vehículo en km/h (PID 010D). Fórmula: A."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x0D, 1)
        return float(a)

    @staticmethod
    def decodificar_temperatura_refrigerante(hex_str: str) -> float:
        """Interpreta la temperatura del refrigerante en °C (PID 0105). Fórmula: A - 40."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x05, 1)
        return float(a - 40)

    @staticmethod
    def decodificar_carga_motor(hex_str: str) -> float:
        """Interpreta el porcentaje de carga calculada del motor (PID 0104). Fórmula: (A * 100) / 255."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x04, 1)
        return round((a * 100.0) / 255.0, 2)

    @staticmethod
    def decodificar_posicion_acelerador(hex_str: str) -> float:
        """Interpreta la posición absoluta de la mariposa en % (PID 0111). Fórmula: (A * 100) / 255."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x11, 1)
        return round((a * 100.0) / 255.0, 2)

    @staticmethod
    def decodificar_maf(hex_str: str) -> float:
        """Interpreta el flujo de masa de aire MAF en g/s (PID 0110). Fórmula: ((A * 256) + B) / 100."""
        a, b = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x10, 2)
        return round(((a * 256) + b) / 100.0, 2)

    @staticmethod
    def decodificar_sensor_o2(hex_str: str) -> float:
        """Interpreta el voltaje del sensor de oxígeno B1S1 en Voltios (PID 0114). Fórmula: A / 200."""
        a, _ = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x14, 2)
        return round(a / 200.0, 3)

    @staticmethod
    def decodificar_iat(hex_str: str) -> float:
        """Interpreta la temperatura del aire de admisión en °C (PID 010F). Fórmula: A - 40."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x0F, 1)
        return float(a - 40)

    @staticmethod
    def decodificar_nivel_combustible(hex_str: str) -> float:
        """Interpreta el nivel de combustible en % (PID 012F). Fórmula: (A * 100) / 255."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x2F, 1)
        return round((a * 100.0) / 255.0, 2)

    @staticmethod
    def decodificar_presion_map(hex_str: str) -> float:
        """Interpreta la presión absoluta del múltiple de admisión en kPa (PID 010B). Fórmula: A."""
        (a,) = EstrategiasProtocolo._extraer_bytes_pid(hex_str, 0x0B, 1)
        return float(a)

    @staticmethod
    def decodificar_dtc_bytes(hex_str: str) -> list[str]:
        """Interpreta los códigos de falla almacenados en la ECU (Servicio 03)."""
        data = EstrategiasProtocolo._bytes(hex_str)
        try:
            start = data.index(0x43) + 1
            data = data[start:]
        except ValueError:
            pass

        # Algunas interfaces incluyen un byte inicial con el número de DTC.
        if len(data) % 2 == 1 and data and data[0] == (len(data) - 1) // 2:
            data = data[1:]

        result = []
        families = "PCBU"

        for i in range(0, len(data) - 1, 2):
            a, b = data[i], data[i + 1]
            if a == 0 and b == 0:
                continue
            family = families[(a >> 6) & 0x03]
            digit = (a >> 4) & 0x03
            result.append(f"{family}{digit}{a & 0x0F:X}{b:02X}")

        return result
