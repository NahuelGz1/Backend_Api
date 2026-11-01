"""Funciones auxiliares para interactuar con la API de TMDB."""

import os
try:
    import requests
except ImportError:
    requests = None

def _pedir_a_tmdb(ruta, api_key, parametros=None):
    """Hace un GET a TMDB. Devuelve (datos, error)."""
    url_base = "https://api.themoviedb.org/3"
    idioma = "es-AR"
    segundos_de_espera = 5

    parametros_completos = {"api_key": api_key, "language": idioma}
    if parametros is not None:
        for clave in parametros:
            parametros_completos[clave] = parametros[clave]

    try:
        respuesta = requests.get(
            url_base + ruta,
            params=parametros_completos,
            timeout=segundos_de_espera,
        )
    except requests.RequestException:
        return None, {"mensaje": "No se pudo conectar con TMDB, probá de nuevo en un rato", "codigo": 502}

    if respuesta.status_code == 401:
        return None, {"mensaje": "La API key de TMDB no es válida", "codigo": 500}
    if respuesta.status_code != 200:
        return None, {"mensaje": f"TMDB respondió con el código {respuesta.status_code}", "codigo": 502}

    try:
        return respuesta.json(), None
    except ValueError:
        return None, {"mensaje": "TMDB devolvió una respuesta que no se pudo leer", "codigo": 502}


def _obtener_nombres_de_generos(api_key):
    """Devuelve ({id_de_genero: nombre}, error)."""
    datos, error = _pedir_a_tmdb("/genre/movie/list", api_key)
    if error:
        return None, error

    diccionario_generos = {}
    generos_lista = datos.get("genres", [])
    for genero in generos_lista:
        id_genero = genero["id"]
        nombre_genero = genero["name"]
        diccionario_generos[id_genero] = nombre_genero

    return diccionario_generos, None


def _formatear_resultado_tmdb(resultado, nombres_de_generos):
    """Pasa un resultado de TMDB a los nombres de nuestra tabla peliculas."""
    ruta_poster = resultado.get("poster_path")
    ids_de_generos = resultado.get("genre_ids")

    # De todos los géneros que trae TMDB nos quedamos con el primero
    primer_genero = None
    if ids_de_generos:
        primer_genero = nombres_de_generos.get(ids_de_generos[0])

    # TMDB solo manda la parte final de la ruta del póster, hay que sumarle la dirección de sus imágenes
    url_imagenes = "https://image.tmdb.org/t/p/w500"
    poster_url = None
    if ruta_poster:
        poster_url = url_imagenes + ruta_poster

    sinopsis = resultado.get("overview")
    if not sinopsis:
        sinopsis = None

    fecha_estreno = resultado.get("release_date")
    if not fecha_estreno:
        fecha_estreno = None

    return {
        "tmdb_id": resultado.get("id"),
        "titulo": resultado.get("title"),
        "sinopsis": sinopsis,
        "poster": poster_url,
        "fecha_estreno": fecha_estreno,
        "genero": primer_genero,
    }


def buscar_peliculas(titulo):
    """Busca películas por título en TMDB. Devuelve (lista de hasta 10, error).

    El título ya tiene que venir validado desde el service.
    """
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        return None, {"mensaje": "Falta configurar la variable de entorno TMDB_API_KEY", "codigo": 500}

    nombres_de_generos, error = _obtener_nombres_de_generos(api_key)
    if error:
        return None, error

    datos, error = _pedir_a_tmdb("/search/movie", api_key, {"query": titulo})
    if error:
        return None, error

    resultados_crudos = datos.get("results", [])

    maximo_de_resultados = 10
    resultados_formateados = []
    contador = 0
    for resultado in resultados_crudos:
        if contador < maximo_de_resultados:
            pelicula_formateada = _formatear_resultado_tmdb(resultado, nombres_de_generos)
            resultados_formateados.append(pelicula_formateada)
            contador += 1

    return resultados_formateados, None

# Alias para compatibilidad
consultar_catalogo_tmdb = buscar_peliculas
