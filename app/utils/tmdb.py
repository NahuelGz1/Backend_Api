"""Funciones auxiliares para interactuar con la API de TMDB."""

import os
import requests

def _pedir_a_tmdb(ruta, api_key, parametros=None):
    """Hace un GET a TMDB. Lanza excepción si falla."""
    url_base = "https://api.themoviedb.org/3"
    idioma = "es-AR"
    segundos_de_espera = 5

    parametros_completos = {"api_key": api_key, "language": idioma}
    if parametros is not None:
        parametros_completos.update(parametros)

    try:
        respuesta = requests.get(
            url_base + ruta,
            params=parametros_completos,
            timeout=segundos_de_espera,
            )
    except requests.RequestException as e:
        raise RuntimeError("No se pudo conectar con TMDB") from e

    if respuesta.status_code == 401:
        raise ValueError("La API key de TMDB no es válida", 500)
    if respuesta.status_code != 200:
        raise RuntimeError(f"TMDB respondió con el código {respuesta.status_code}")

    try:
        return respuesta.json()
    except ValueError as e:
        raise RuntimeError("TMDB devolvió una respuesta que no se pudo leer") from e


def _obtener_nombres_de_generos(api_key):
    """Devuelve un diccionario {id_de_genero: nombre}."""
    datos = _pedir_a_tmdb("/genre/movie/list", api_key)
    diccionario_generos = {}
    generos_lista = datos.get("genres", [])
    for genero in generos_lista:
        diccionario_generos[genero["id"]] = genero["name"]
    return diccionario_generos


def _formatear_resultado_tmdb(resultado, nombres_de_generos):
    """Pasa un resultado de TMDB al formato estandarizado."""
    ruta_poster = resultado.get("poster_path")
    ids_de_generos = resultado.get("genre_ids")

    primer_genero = None
    if ids_de_generos:
        primer_genero = nombres_de_generos.get(ids_de_generos[0])

    poster_url = None
    if ruta_poster:
        poster_url = f"https://image.tmdb.org/t/p/w500{ruta_poster}"

    return {
        "tmdb_id": resultado.get("id"),
        "titulo": resultado.get("title"),
        "sinopsis": resultado.get("overview") or None,
        "poster": poster_url,
        "fecha_estreno": resultado.get("release_date") or None,
        "genero": primer_genero,
    }


def buscar_peliculas(titulo):
    """Busca películas por título en TMDB. Devuelve lista de hasta 10 resultados."""
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise ValueError("Falta configurar la variable de entorno TMDB_API_KEY", 500)

    nombres_de_generos = _obtener_nombres_de_generos(api_key)
    datos = _pedir_a_tmdb("/search/movie", api_key, {"query": titulo})
    resultados_crudos = datos.get("results", [])

    resultados_formateados = []
    for resultado in resultados_crudos[:10]:
        resultados_formateados.append(_formatear_resultado_tmdb(resultado, nombres_de_generos))

    return resultados_formateados

# Alias para compatibilidad
consultar_catalogo_tmdb = buscar_peliculas