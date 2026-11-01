from datetime import datetime, timedelta, timezone
from db import ejecutar_consulta, ejecutar_mutacion


def _ahora():
    """Devuelve la hora actual de Argentina (UTC-3) como datetime sin zona horaria."""
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _sql_funciones_vigentes(solo_una_pelicula=False):
    """Arma el SQL de las funciones vigentes."""
    sql = """
          SELECT funciones.id, funciones.id_pelicula, funciones.fecha_hora_proyeccion,
                 salas.nombre AS sala, salas.local, salas.capacidad
          FROM funciones
                   JOIN salas ON salas.id = funciones.id_sala
          WHERE funciones.fecha_hora_proyeccion > %s \
          """
    if solo_una_pelicula:
        sql = sql + " AND funciones.id_pelicula = %s"

    return sql + " ORDER BY funciones.fecha_hora_proyeccion"


def listar_peliculas_en_cartelera():
    """Películas que tienen al menos una función vigente."""
    sql = """
          SELECT peliculas.id, peliculas.titulo, peliculas.sinopsis, peliculas.poster, peliculas.duracion,
                 peliculas.clasificacion, peliculas.genero
          FROM peliculas
          WHERE EXISTS (
              SELECT 1
              FROM funciones
              WHERE funciones.id_pelicula = peliculas.id
                AND funciones.fecha_hora_proyeccion > %s
          )
          ORDER BY peliculas.titulo \
          """
    return ejecutar_consulta(sql, (_ahora(),))


def listar_funciones_vigentes():
    """Todas las funciones vigentes, de todas las películas."""
    sql_completo = _sql_funciones_vigentes()
    return ejecutar_consulta(sql_completo, (_ahora(),))


def listar_funciones_vigentes_de_pelicula(pelicula_id):
    sql_completo = _sql_funciones_vigentes(solo_una_pelicula=True)
    return ejecutar_consulta(sql_completo, (_ahora(), pelicula_id))


def buscar_por_id(pelicula_id):
    """Devuelve la película como diccionario, o None si no existe."""
    sql = """
          SELECT id, titulo, sinopsis, poster, duracion, clasificacion, genero
          FROM peliculas
          WHERE id = %s \
          """
    filas = ejecutar_consulta(sql, (pelicula_id,))

    if len(filas) > 0:
        return filas[0]
    else:
        return None


def existe_pelicula(titulo, duracion):
    """Dice si ya hay una película con ese título y esa duración."""
    sql = """
          SELECT id
          FROM peliculas
          WHERE titulo = %s AND duracion = %s \
          """
    filas = ejecutar_consulta(sql, (titulo, duracion))
    return len(filas) > 0


def insertar(pelicula):
    """Guarda una película nueva y devuelve su id."""
    sql = """
          INSERT INTO peliculas (titulo, sinopsis, poster, duracion, clasificacion, genero)
          VALUES (%s, %s, %s, %s, %s, %s) \
          """
    parametros = (
        pelicula["titulo"],
        pelicula["sinopsis"],
        pelicula["poster"],
        pelicula["duracion"],
        pelicula["clasificacion"],
        pelicula["genero"],
    )
    return ejecutar_mutacion(sql, parametros)