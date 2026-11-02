"""Validaciones de los datos de funciones (POST y PATCH /funciones)."""

from app.utils.dates import string_a_datetime


def _validar_id(datos, campo, errores, obligatorio):
    """Devuelve el id si es un entero mayor a 0, o None si no vino o es inválido."""
    valor = datos.get(campo)

    if valor is None:
        if obligatorio:
            errores[campo] = "Es obligatorio"
        return None

    # Con type() quedan afuera los bool (True/False), los decimales y los textos
    if type(valor) != int or valor <= 0:
        errores[campo] = "Tiene que ser un número entero mayor a 0"
        return None

    return valor


def _validar_fecha_hora(datos, errores, obligatorio):
    """Devuelve la fecha y hora como datetime, o None si no vino o es inválida."""
    valor = datos.get("fecha_hora_proyeccion")

    if valor is None:
        if obligatorio:
            errores["fecha_hora_proyeccion"] = "Es obligatorio"
        return None

    if type(valor) != str:
        errores["fecha_hora_proyeccion"] = "Tiene que ser un texto con formato YYYY-MM-DD HH:MM:SS"
        return None

    try:
        return string_a_datetime(valor.strip())
    except ValueError:
        # strptime lanza ValueError si el texto no respeta el formato o la fecha no existe (ej: 31 de febrero)
        errores["fecha_hora_proyeccion"] = "Tiene que tener formato YYYY-MM-DD HH:MM:SS y ser una fecha real"
        return None


def validar_funcion_nueva(datos):
    """Valida el JSON de POST /funciones. Los tres campos son obligatorios.

    Devuelve (funcion, errores): si no hay errores, errores es un diccionario vacío.
    """
    if type(datos) != dict:
        return None, {"cuerpo": "Tiene que ser un JSON con los datos de la función"}

    errores = {}

    funcion = {
        "id_pelicula": _validar_id(datos, "id_pelicula", errores, obligatorio=True),
        "id_sala": _validar_id(datos, "id_sala", errores, obligatorio=True),
        "fecha_hora_proyeccion": _validar_fecha_hora(datos, errores, obligatorio=True),
    }

    if len(errores) > 0:
        return None, errores

    return funcion, {}


def validar_cambios_funcion(datos):
    """Valida el JSON de PATCH /funciones/<id>. Todos los campos son opcionales,
    pero tiene que venir al menos uno.

    Devuelve (cambios, errores): cambios solo tiene los campos que vinieron.
    """
    if type(datos) != dict:
        return None, {"cuerpo": "Tiene que ser un JSON con los datos a modificar"}

    campos_permitidos = ("id_pelicula", "id_sala", "fecha_hora_proyeccion")

    # Nos fijamos si vino al menos uno de los campos que se pueden modificar
    vino_algun_campo = False
    for campo in campos_permitidos:
        if campo in datos:
            vino_algun_campo = True

    if not vino_algun_campo:
        return None, {"cuerpo": "Tiene que enviar al menos uno de estos campos: " + ", ".join(campos_permitidos)}

    errores = {}
    cambios = {}

    if "id_pelicula" in datos:
        cambios["id_pelicula"] = _validar_id(datos, "id_pelicula", errores, obligatorio=True)
    if "id_sala" in datos:
        cambios["id_sala"] = _validar_id(datos, "id_sala", errores, obligatorio=True)
    if "fecha_hora_proyeccion" in datos:
        cambios["fecha_hora_proyeccion"] = _validar_fecha_hora(datos, errores, obligatorio=True)

    if len(errores) > 0:
        return None, errores

    return cambios, {}
