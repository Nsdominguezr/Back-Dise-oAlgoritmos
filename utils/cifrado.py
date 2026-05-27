# cifrado.py

CLAVE_SECRETA = "97342722LaCucarachaNoPodiaCaminar"

# Definimos nuestro propio alfabeto de 62 caracteres (A-Z, a-z, 0-9)
ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789*,.-_+@#%&()=!"  # Total: 62 caracteres únicos

# Inicializamos la semilla con el ID de la clave
_ESTADO_CAOS = id(CLAVE_SECRETA)

def generar_iv_matematico():
    """Generador Lineal Congruencial para aleatoriedad manual."""
    global _ESTADO_CAOS
    multiplicador = 1103515245
    incremento = 12345
    modulo = 2**31
    _ESTADO_CAOS = (multiplicador * _ESTADO_CAOS + incremento) % modulo
    return _ESTADO_CAOS % 256

def byte_a_base62(byte):
    """Convierte un número (0-255) en 2 caracteres del alfabeto."""
    # Usamos división y residuo para obtener dos índices del alfabeto
    # Como 62 * 62 = 3844, siempre podemos representar 0-255 con 2 letras
    primero = byte // 62
    segundo = byte % 62
    return ALFABETO[primero] + ALFABETO[segundo]

def base62_a_byte(par_caracteres):
    """Convierte 2 caracteres del alfabeto de vuelta a un número (0-255)."""
    # Buscamos la posición (índice) de cada letra en nuestro ALFABETO
    indice1 = ALFABETO.find(par_caracteres[0])
    indice2 = ALFABETO.find(par_caracteres[1])
    return (indice1 * 62) + indice2

def encriptar(texto):
    clave = CLAVE_SECRETA
    resultado_alfa = ""
    
    # 1. Generamos el IV aleatorio
    iv = generar_iv_matematico()
    ultimo_cifrado = iv
    
    # 2. Guardamos el IV convertido a nuestras letras (2 caracteres)
    resultado_alfa += byte_a_base62(iv)
    
    for i in range(len(texto)):
        char_texto = ord(texto[i])
        char_clave = ord(clave[i % len(clave)])
        
        # Mezcla XOR con encadenamiento
        cifrado = char_texto ^ char_clave ^ ultimo_cifrado
        
        # Convertimos el byte cifrado a 2 caracteres de nuestro alfabeto
        resultado_alfa += byte_a_base62(cifrado)
        
        # Actualizamos el rastro para la siguiente letra
        ultimo_cifrado = cifrado
        
    return resultado_alfa

def desencriptar(texto_alfa):
    try:
        clave = CLAVE_SECRETA
        resultado = ""
        
        # Extraemos el IV (los primeros 2 caracteres)
        iv_letras = texto_alfa[:2]
        ultimo_cifrado = base62_a_byte(iv_letras)
        
        # El resto es el mensaje (leído de 2 en 2 caracteres)
        cuerpo = texto_alfa[2:]
        
        for i in range(0, len(cuerpo), 2):
            par = cuerpo[i:i+2]
            char_cifrado = base62_a_byte(par)
            
            char_clave = ord(clave[(i//2) % len(clave)])
            
            # Revertimos el XOR
            original = char_cifrado ^ char_clave ^ ultimo_cifrado
            resultado += chr(original)
            
            ultimo_cifrado = char_cifrado
            
        return resultado
    except:
        return "ERROR: El código contiene caracteres inválidos o la clave es incorrecta."