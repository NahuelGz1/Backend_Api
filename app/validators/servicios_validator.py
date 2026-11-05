def _validar_nombre(datos: dict, errores: dict):
    #Devuelve el nombre si es un texto válido no vacío (máx 100 caracteres)
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
    #Devuelve la descripción limpia, o None si no vino o esta vacía
    valor = datos.get("descripcion")

    if valor is None:
        return None

    if not isinstance(valor, str):
        errores["descripcion"] = "Tiene que ser un texto"
        return None

    valor = valor.strip()
    if not valor:
        return None

    return valor


def _validar_precio(datos: dict, errores: dict):
    #Devuelve el precio si es un número válido mayor a 0 y dentro del rango DECIMAL(10,2)
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
    #Valida el JSON de POST y PUT /servicios, obligatorios: nombre y precio. Opcional: descripción.
    
    if not isinstance(datos, dict):
        return None, {"cuerpo": "Tiene que ser un JSON con los datos del servicio"}

    errores = {}

    servicio = {
        "nombre": _validar_nombre(datos, errores),
        "descripcion": _validar_descripcion(datos, errores),
        "precio": _validar_precio(datos, errores),
    }

    if errores:
        return None, errores

    return servicio, {}