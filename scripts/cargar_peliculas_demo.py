"""Carga el catálogo de demostración y programa sus películas de cartelera."""

from app.db import obtener_conexion
from scripts.catalogo_peliculas_demo import PELICULAS, URL_POSTER
from scripts.generar_funciones_demo import generar_funciones


def cargar_catalogo():
    conexion = obtener_conexion()
    ids_programables = []
    creadas = []
    omitidas = []
    try:
        with conexion.cursor() as cursor:
            for titulo, duracion, clasificacion, genero, poster, programar in PELICULAS:
                cursor.execute(
                    "SELECT id, duracion, activo, eliminada FROM peliculas WHERE titulo = %s FOR UPDATE",
                    (titulo,),
                )
                coincidencias = cursor.fetchall()
                if coincidencias:
                    if (len(coincidencias) != 1 or coincidencias[0]["duracion"] != duracion
                            or not coincidencias[0]["activo"] or coincidencias[0]["eliminada"]):
                        omitidas.append(titulo)
                        continue
                    pelicula_id = coincidencias[0]["id"]
                    cursor.execute(
                        "UPDATE peliculas SET poster = %s WHERE id = %s AND (poster IS NULL OR poster = '')",
                        (URL_POSTER + poster, pelicula_id),
                    )
                else:
                    cursor.execute(
                        "INSERT INTO peliculas (titulo, duracion, clasificacion, genero, poster) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (titulo, duracion, clasificacion, genero, URL_POSTER + poster),
                    )
                    pelicula_id = cursor.lastrowid
                    creadas.append(titulo)
                if programar:
                    ids_programables.append(pelicula_id)
        conexion.commit()
        return creadas, omitidas, ids_programables
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    creadas, omitidas, ids = cargar_catalogo()
    print(f"Películas agregadas: {len(creadas)}")
    for titulo in omitidas:
        print(f"No se modificó ni programó por coincidencia ambigua, datos distintos o estado inactivo: {titulo}")
    try:
        funciones = generar_funciones(ids_peliculas_demo=ids)
    except Exception:
        print("El catálogo ya fue guardado, pero falló la generación de funciones. Revisá el error y volvé a ejecutar el comando.")
        raise
    for fecha, local, sala, pelicula in funciones:
        print(f"{fecha:%d/%m/%Y %H:%M} | {local} | {sala} | {pelicula}")
    print(f"Funciones creadas: {len(funciones)}")
