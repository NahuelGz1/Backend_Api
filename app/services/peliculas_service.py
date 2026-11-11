"""Lógica de películas: cartelera, detalle, alta y búsqueda en TMDB."""

from app.repositories import peliculas_repository as repositorio
from app.utils import tmdb
from app.utils.dates import datetime_a_string
from app.validators import peliculas_validator as validador


# autocompleta faltantes
def _completar_datos_faltantes_con_tmdb(pelicula: dict):
    if pelicula.get("poster") and pelicula.get("sinopsis"):
        return

    titulo = pelicula.get("titulo")
    try:
        resultados = tmdb.buscar_peliculas(titulo)

        if resultados:
            mejor = resultados[0]
            nueva_sinopsis = mejor.get("sinopsis")
            nuevo_poster = mejor.get("poster")

            if nuevo_poster and not pelicula.get("poster"):
                pelicula["poster"] = nuevo_poster
            if nueva_sinopsis and not pelicula.get("sinopsis"):
                pelicula["sinopsis"] = nueva_sinopsis

            repositorio.actualizar_datos_tmdb(pelicula["id"], nueva_sinopsis, nuevo_poster)

    except Exception:
        pass


# ----------- Películas propias --------------------------------------

def _funcion_a_dict(fila: dict) -> dict:
    return {
        "id": fila["id"],
        "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
        "sala": fila["sala"],
        "local": fila["local"],
        "capacidad": fila["capacidad"],
    }


def _pelicula_a_dict(fila: dict, funciones: list) -> dict:
    return {
        "id": fila["id"],
        "titulo": fila["titulo"],
        "sinopsis": fila["sinopsis"],
        "poster": fila["poster"],
        "duracion": fila["duracion"],
        "clasificacion": fila["clasificacion"],
        "genero": fila["genero"],
        "activo": bool(fila.get("activo", True)),
        "eliminada": bool(fila.get("eliminada", False)),
        "funciones": funciones,
    }


def obtener_cartelera() -> list:
    """Películas que tienen funciones vigentes, cada una con sus funciones."""
    peliculas = repositorio.listar_peliculas_en_cartelera()
    funciones_vigentes = repositorio.listar_funciones_vigentes()

    funciones_por_pelicula = {}
    for fila in funciones_vigentes:
        id_pelicula = fila["id_pelicula"]
        if id_pelicula not in funciones_por_pelicula:
            funciones_por_pelicula[id_pelicula] = []

        funciones_por_pelicula[id_pelicula].append(_funcion_a_dict(fila))

    resultado_final = []
    for pelicula in peliculas:
        # revisa tmdb al vuelo
        _completar_datos_faltantes_con_tmdb(pelicula)

        id_pelicula = pelicula["id"]
        funciones_de_esta_pelicula = funciones_por_pelicula.get(id_pelicula, [])
        resultado_final.append(_pelicula_a_dict(pelicula, funciones_de_esta_pelicula))

    return resultado_final


def obtener_pelicula(pelicula_id: int) -> dict:
    """Una película con sus funciones vigentes. Lanza ValueError 404 si no existe."""
    pelicula = repositorio.buscar_por_id(pelicula_id)
    if pelicula is None:
        raise ValueError(f"No existe la película {pelicula_id}", 404)

    # revisa tmdb al vuelo
    _completar_datos_faltantes_con_tmdb(pelicula)

    filas = repositorio.listar_funciones_vigentes_de_pelicula(pelicula_id)
    lista_funciones = [_funcion_a_dict(fila) for fila in filas]

    return _pelicula_a_dict(pelicula, lista_funciones)


def crear_pelicula(datos: dict) -> dict:
    """Valida los datos, guarda la película y la devuelve ya creada."""
    pelicula, errores = validador.validar_pelicula(datos)
    if errores:
        raise ValueError("Hay datos inválidos", 400, errores)

    if repositorio.existe_pelicula(pelicula["titulo"], pelicula["duracion"]):
        raise ValueError("Ya existe una película con ese título y esa duración", 409)

    nuevo_id = repositorio.insertar(pelicula)

    # Retornamos directamente el objeto creado sin consultar funciones innecesariamente
    pelicula["id"] = nuevo_id
    pelicula["funciones"] = []
    return pelicula


def listar_peliculas_admin() -> list:
    return [_pelicula_a_dict(fila, []) for fila in repositorio.listar_todas()]


def cambiar_estado_pelicula(pelicula_id: int, activo: bool) -> dict:
    pelicula = repositorio.buscar_por_id(pelicula_id)
    if pelicula is None:
        raise ValueError("Película no encontrada", 404)
    repositorio.cambiar_estado(pelicula_id, activo)
    pelicula["activo"] = activo
    return _pelicula_a_dict(pelicula, [])


def eliminar_pelicula(pelicula_id: int) -> dict:
    pelicula = repositorio.buscar_por_id(pelicula_id)
    if pelicula is None:
        raise ValueError("Película no encontrada", 404)
    repositorio.eliminar(pelicula_id)
    pelicula["activo"] = False
    pelicula["eliminada"] = True
    return _pelicula_a_dict(pelicula, [])


# ------- Búsqueda en TMDB (API externa) ---------------------------

def buscar_peliculas_en_tmdb(titulo: str) -> list:
    """Valida el título y realiza la búsqueda en TMDB."""
    titulo_validado, errores = validador.validar_titulo_busqueda(titulo)
    if errores:
        raise ValueError("Hay datos inválidos", 400, errores)

    return tmdb.buscar_peliculas(titulo_validado)


def obtener_proximos_estrenos() -> list:
    """Devuelve la lista de próximos estrenos recuperados desde la API de TMDB."""
    try:
        estrenos_crudos = tmdb.obtener_proximos_estrenos()
        estrenos_formateados = []
        for item in estrenos_crudos:
            estrenos_formateados.append({
                "id": item.get("tmdb_id"),
                "titulo": item.get("titulo"),
                "sinopsis": item.get("sinopsis"),
                "poster": item.get("poster"),
                "fecha_estreno": item.get("fecha_estreno"),
                "genero": item.get("genero")
            })
        return estrenos_formateados
    except Exception:
        return []
