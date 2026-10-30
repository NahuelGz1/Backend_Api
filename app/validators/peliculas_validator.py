"""Validaciones de los datos de películas."""


def _validar_texto(datos, campo, errores, obligatorio=False):
    """Devuelve el texto sin espacios de más, o None si no vino o es inválido."""
    valor = datos.get(campo)

    # Si vino algo que no es texto (un número, una lista, etc.)
    if valor is not None and type(valor) != str:
        errores[campo] = "Tiene que ser un texto"
        return None

    # Le sacamos los espacios de más a los costados
    if valor is not None:
        valor = valor.strip()

    # Si no vino, o quedó vacío después del strip
    if valor is None or valor == "":
        if obligatorio:
            errores[campo] = "Es obligatorio"
        return None

    # Validamos el largo máximo permitido (el de las columnas VARCHAR de la tabla peliculas)
    largos_maximos = {"titulo": 150, "poster": 255, "genero": 50}
    maximo = largos_maximos.get(campo)
    if maximo is not None:
        if len(valor) > maximo:
            errores[campo] = f"Puede tener como máximo {maximo} caracteres"
            return None

    return valor


def _validar_duracion(datos, errores, obligatorio=False):
    valor = datos.get("duracion")

    if valor is None:
        if obligatorio:
            errores["duracion"] = "Es obligatorio"
        return None

    # Con type() el valor tiene que ser exactamente un int: True y False (que son de tipo bool)
    # y los decimales como 120.5 quedan afuera
    if type(valor) != int or valor <= 0:
        errores["duracion"] = "Tiene que ser un número entero mayor a 0 (en minutos)"
        return None

    return valor


def _validar_clasificacion(datos, errores, obligatorio=False):
    clasificaciones_validas = ("ATP", "+13", "+16", "+18")
    valor = _validar_texto(datos, "clasificacion", errores, obligatorio)

    if valor is not None:
        # Verificamos si la clasificación está dentro de las válidas
        encontrado = False
        for clasificacion in clasificaciones_validas:
            if valor == clasificacion:
                encontrado = True

        if not encontrado:
            opciones = ", ".join(clasificaciones_validas)
            errores["clasificacion"] = f"Tiene que ser una de estas: {opciones}"
            return None

    return valor


def validar_pelicula(datos):
    """Valida el JSON de POST /peliculas.

    Obligatorios: título, duración, clasificación y género (la cartelera y el
    dashboard de ventas por género los necesitan). Opcionales: sinopsis y póster.
    """
    if type(datos) != dict:
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

    # Usamos len() para ver si el diccionario de errores tiene elementos
    if len(errores) > 0:
        return None, errores

    return pelicula, {}


def validar_titulo_busqueda(titulo):
    """Valida el parámetro ?titulo= de GET /peliculas/buscar-externa."""
    if titulo is None:
        titulo = ""
    else:
        titulo = titulo.strip()

    if len(titulo) < 2:
        return None, {"titulo": "Es obligatorio (mínimo 2 caracteres)"}

    return titulo, {}
