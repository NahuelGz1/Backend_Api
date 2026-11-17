import base64
import re


_IMAGEN_DATA_URI = re.compile(
    r"^data:image/(jpeg|png);base64,([A-Za-z0-9+/=\s]+)$",
    re.IGNORECASE,
)
_MAX_IMAGEN_BYTES = 5 * 1024 * 1024


def _validar_imagen(datos: dict, errores: dict):
    valor = datos.get("imagen_url")
    if valor is None or valor == "":
        return None
    if not isinstance(valor, str):
        errores["imagen_url"] = "La imagen no es válida"
        return None
    coincidencia = _IMAGEN_DATA_URI.fullmatch(valor.strip())
    if not coincidencia:
        errores["imagen_url"] = "La imagen debe ser JPG o PNG"
        return None
    try:
        contenido = base64.b64decode(coincidencia.group(2), validate=True)
    except (ValueError, TypeError):
        errores["imagen_url"] = "La imagen no es válida"
        return None
    if len(contenido) > _MAX_IMAGEN_BYTES:
        errores["imagen_url"] = "La imagen no puede superar los 5 MB"
        return None
    return valor.strip()


def _validar_nombre(datos: dict, errores: dict):
    valor = datos.get("nombre")
    if valor is None:
        errores["nombre"] = "Es obligatorio"
        return None
    if not isinstance(valor, str):
        errores["nombre"] = "Tiene que ser un texto"
        return None
    valor = valor.strip()
    if not valor:
        errores["nombre"] = "Es obligatorio"
        return None
    if len(valor) > 100:
        errores["nombre"] = "Puede tener como máximo 100 caracteres"
        return None
    return valor


def _validar_descripcion(datos: dict, errores: dict):
    valor = datos.get("descripcion")
    if valor is None:
        return None
    if not isinstance(valor, str):
        errores["descripcion"] = "Tiene que ser un texto"
        return None
    valor = valor.strip()
    return valor or None


def _validar_precio(datos: dict, errores: dict):
    valor = datos.get("precio")
    if valor is None:
        errores["precio"] = "Es obligatorio"
        return None
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        errores["precio"] = "Tiene que ser un número"
        return None
    if valor <= 0:
        errores["precio"] = "Tiene que ser mayor a 0"
        return None
    if valor >= 100000000:
        errores["precio"] = "Es demasiado grande"
        return None
    return valor


def validar_servicio(datos: dict) -> tuple:
    if not isinstance(datos, dict):
        return None, {"cuerpo": "Tiene que ser un JSON con los datos del servicio"}

    errores = {}
    servicio = {
        "nombre": _validar_nombre(datos, errores),
        "descripcion": _validar_descripcion(datos, errores),
        "precio": _validar_precio(datos, errores),
        "imagen_url": _validar_imagen(datos, errores),
    }
    if errores:
        return None, errores
    return servicio, {}
