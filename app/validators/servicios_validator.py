def _validar_nombre(datos, errores):
    valor = datos.get("nombre")

    if valor is None:
        errores["nombre"] = "Es obligatorio"
        return None

    if type(valor) != str:
        errores["nombre"] = "Tiene que ser un texto"
        return None

    valor = valor.strip()
    if valor == "":
        errores["nombre"] = "Es obligatorio"
        return None

    # 100 es el largo máximo de la columna nombre en la tabla servicios
    if len(valor) > 100:
        errores["nombre"] = "Puede tener como máximo 100 caracteres"
        return None

    return valor


def _validar_descripcion(datos, errores):
    valor = datos.get("descripcion")

    if valor is None:
        return None

    if type(valor) != str:
        errores["descripcion"] = "Tiene que ser un texto"
        return None

    valor = valor.strip()
    if valor == "":
        return None

    return valor


def _validar_precio(datos, errores):
    valor = datos.get("precio")

    if valor is None:
        errores["precio"] = "Es obligatorio"
        return None

    # Con type() quedan afuera True y False (que son de tipo bool) y los textos
    if type(valor) != int and type(valor) != float:
        errores["precio"] = "Tiene que ser un número"
        return None

    if valor <= 0:
        errores["precio"] = "Tiene que ser mayor a 0"
        return None

    # La columna precio es DECIMAL(10, 2): como mucho 8 dígitos antes de la coma
    if valor >= 100000000:
        errores["precio"] = "Es demasiado grande"
        return None

    return valor


def validar_servicio(datos):
    """Valida el JSON de POST y PUT /servicios.

    Obligatorios: nombre y precio. Opcional: descripción.
    """
    if type(datos) != dict:
        return None, {"cuerpo": "Tiene que ser un JSON con los datos del servicio"}

    errores = {}

    servicio = {
        "nombre": _validar_nombre(datos, errores),
        "descripcion": _validar_descripcion(datos, errores),
        "precio": _validar_precio(datos, errores),
    }

    if len(errores) > 0:
        return None, errores

    return servicio, {}