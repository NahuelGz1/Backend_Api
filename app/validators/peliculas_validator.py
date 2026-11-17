"""Validaciones de los datos de películas."""


def _validar_texto(datos: dict, campo: str, errores: dict, obligatorio: bool = False):
    """Devuelve el texto sin espacios de más, o None si no vino o es inválido."""
    valor = datos.get(campo)

    if valor is not None and not isinstance(valor, str):
        errores[campo] = "Tiene que ser un texto"
        return None

    if valor is not None:
        valor = valor.strip()

    if not valor:
        if obligatorio:
            errores[campo] = "Es obligatorio"
        return None

    largos_maximos = {"titulo": 150, "poster": 255, "genero": 50}
    maximo = largos_maximos.get(campo)
    if maximo is not None and len(valor) > maximo:
        errores[campo] = f"Puede tener como máximo {maximo} caracteres"
        return None

    return valor


def _validar_duracion(datos: dict, errores: dict, obligatorio: bool = False):
    valor = datos.get("duracion")

    if valor is None:
        if obligatorio:
            errores["duracion"] = "Es obligatorio"
        return None

    if not isinstance(valor, int) or isinstance(valor, bool) or valor <= 0:
        errores["duracion"] = "Tiene que ser un número entero mayor a 0 (en minutos)"
        return None

    return valor


def _validar_clasificacion(datos: dict, errores: dict, obligatorio: bool = False):
    clasificaciones_validas = ("ATP", "+13", "+16", "+18")
    valor = _validar_texto(datos, "clasificacion", errores, obligatorio)

    if valor is not None and valor not in clasificaciones_validas:
        opciones = ", ".join(clasificaciones_validas)
        errores["clasificacion"] = f"Tiene que ser una de estas: {opciones}"
        return None

    return valor


def validar_pelicula(datos: dict) -> tuple:
    """Valida el JSON de POST /peliculas."""
    if not isinstance(datos, dict):
        return None, {"cuerpo": "Tiene que ser un JSON con los datos de la película"}

    errores = {}

    pelicula = {
        "titulo": _validar_texto(datos, "titulo", errores, obligatorio=True),
        "sinopsis": _validar_texto(datos, "sinopsis", errores),
        "poster": _validar_texto(datos, "poster", errores),
        "duracion": _validar_duracion(datos, errores, obligatorio=True),
        "clasificacion": _validar_clasificacion(datos, errores, obligatorio=True),
        "genero": _validar_texto(datos, "genero", errores, obligatorio=True),
    }

    if errores:
        return None, errores

    return pelicula, {}


def validar_titulo_busqueda(titulo: str) -> tuple:
    """Valida el parámetro ?titulo= de GET /peliculas/buscar-externa."""
    titulo_limpio = (titulo or "").strip()

    if len(titulo_limpio) < 2:
        return None, {"titulo": "Es obligatorio (mínimo 2 caracteres)"}

    return titulo_limpio, {}