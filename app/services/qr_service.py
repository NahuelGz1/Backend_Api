def validar_codigo_qr_recibido(codigo_qr):
    """
    Comprueba que se haya recibido un código QR
    con contenido válido.
    """

    if not isinstance(codigo_qr, str):
        raise ValueError("El código QR debe ser una cadena de texto")

    if codigo_qr.strip() == "":
        raise ValueError("No se recibió un código QR válido")

    return codigo_qr.strip()


def validar_estado_entrada(estado):
    """
    Comprueba si una entrada está en condiciones
    de utilizarse para ingresar al cine.
    """

    if estado == "cancelada":
        raise ValueError("La entrada fue cancelada")

    if estado == "utilizada":
        raise ValueError("La entrada ya fue utilizada")

    if estado != "comprada":
        raise ValueError("El estado de la entrada no es válido")

    return True