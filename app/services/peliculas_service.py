"""Lógica de películas: cartelera, detalle, alta y búsqueda en TMDB."""

from app.repositories import peliculas_repository as repositorio
from app.validators import peliculas_validator as validador
from app.utils import tmdb


# -----------Películas propias (las que están en nuestra propia base de datos)--------------------------------------

def _funcion_a_dict(fila):
    return {
        "id": fila["id"],
        # isoformat() se encarga de pasar el objeto fecha de Python a texto plano con formato estándar (ej: "2026-12-04T16:00:00") para que el front lo lea bien
        "fecha_hora_proyeccion": fila["fecha_hora_proyeccion"].isoformat(),
        "sala": fila["sala"],
        "local": fila["local"],
        "capacidad": fila["capacidad"],
    }


def _pelicula_a_dict(fila, funciones):
    return {
        "id": fila["id"],
        "titulo": fila["titulo"],
        "sinopsis": fila["sinopsis"],
        "poster": fila["poster"],
        "duracion": fila["duracion"],
        "clasificacion": fila["clasificacion"],
        "genero": fila["genero"],
        "funciones": funciones,
    }


def obtener_cartelera():
    """Películas que tienen funciones vigentes, cada una con sus funciones."""
    peliculas = repositorio.listar_peliculas_en_cartelera()
    funciones_vigentes = repositorio.listar_funciones_vigentes()

    # Agrupamos las funciones por película
    funciones_por_pelicula = {}
    for fila in funciones_vigentes:
        id_pelicula = fila["id_pelicula"]
        if id_pelicula not in funciones_por_pelicula:
            funciones_por_pelicula[id_pelicula] = []

        funcion_dict = _funcion_a_dict(fila)
        funciones_por_pelicula[id_pelicula].append(funcion_dict)

    # Armamos la lista final
    resultado_final = []
    for pelicula in peliculas:
        id_pelicula = pelicula["id"]

        # Buscamos si tiene funciones, sino dejamos una lista vacía
        funciones_de_esta_pelicula = []
        if id_pelicula in funciones_por_pelicula:
            funciones_de_esta_pelicula = funciones_por_pelicula[id_pelicula]

        pelicula_dict = _pelicula_a_dict(pelicula, funciones_de_esta_pelicula)
        resultado_final.append(pelicula_dict)

    return resultado_final


def obtener_pelicula(pelicula_id):
    """Una película con sus funciones vigentes. Devuelve (pelicula, error)."""
    pelicula = repositorio.buscar_por_id(pelicula_id)
    if pelicula is None:
        return None, {"mensaje": f"No existe la película {pelicula_id}", "codigo": 404}

    filas = repositorio.listar_funciones_vigentes_de_pelicula(pelicula_id)

    # Convertimos las filas de funciones
    lista_funciones = []
    for fila in filas:
        funcion_dict = _funcion_a_dict(fila)
        lista_funciones.append(funcion_dict)

    pelicula_dict = _pelicula_a_dict(pelicula, lista_funciones)
    return pelicula_dict, None


def crear_pelicula(datos):
    """Valida los datos, guarda la película y la devuelve ya creada."""
    pelicula, errores = validador.validar_pelicula(datos)
    if errores:
        return None, {"mensaje": "Hay datos inválidos", "codigo": 400, "detalles": errores}

    # Dos películas con el mismo título y la misma duración las tomamos como la misma
    if repositorio.existe_pelicula(pelicula["titulo"], pelicula["duracion"]):
        return None, {"mensaje": "Ya existe una película con ese título y esa duración", "codigo": 409}

    nuevo_id = repositorio.insertar(pelicula)
    return obtener_pelicula(nuevo_id)


# ------- Búsqueda en TMDB (API externa) ---------------------------

def buscar_peliculas_en_tmdb(titulo):
    """Valida el título y le pide la búsqueda a utils/tmdb.py. Devuelve (lista, error)."""
    titulo, errores = validador.validar_titulo_busqueda(titulo)
    if errores:
        return None, {"mensaje": "Hay datos inválidos", "codigo": 400, "detalles": errores}

    return tmdb.buscar_peliculas(titulo)
