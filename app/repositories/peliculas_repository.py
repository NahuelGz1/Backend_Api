from datetime import datetime, timedelta, timezone
from app.db import ejecutar_consulta, ejecutar_mutacion


def _ahora() -> datetime:
    """Devuelve la hora actual de Argentina (UTC-3) como datetime sin zona horaria."""
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _sql_funciones_vigentes(solo_una_pelicula: bool = False) -> str:
    """Arma la consulta SQL para obtener funciones vigentes."""
    sql = """
          SELECT funciones.id, funciones.id_pelicula, funciones.fecha_hora_proyeccion,
                 salas.nombre AS sala, salas.local, salas.capacidad
          FROM funciones
                   JOIN salas ON salas.id = funciones.id_sala
          WHERE funciones.fecha_hora_proyeccion > %s \
          """
    if solo_una_pelicula:
        sql += " AND funciones.id_pelicula = %s"

    return sql + " ORDER BY funciones.fecha_hora_proyeccion"


def listar_peliculas_en_cartelera() -> list[dict]:
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


def listar_funciones_vigentes() -> list[dict]:
    """Todas las funciones vigentes de todas las películas."""
    sql_completo = _sql_funciones_vigentes()
    return ejecutar_consulta(sql_completo, (_ahora(),))


def listar_funciones_vigentes_de_pelicula(pelicula_id: int) -> list[dict]:
    """Funciones vigentes asociadas a una película específica."""
    sql_completo = _sql_funciones_vigentes(solo_una_pelicula=True)
    return ejecutar_consulta(sql_completo, (_ahora(), pelicula_id))


def buscar_por_id(pelicula_id: int) -> dict | None:
    """Devuelve la película como diccionario, o None si no existe."""
    sql = """
          SELECT id, titulo, sinopsis, poster, duracion, clasificacion, genero
          FROM peliculas
          WHERE id = %s \
          """
    filas = ejecutar_consulta(sql, (pelicula_id,))
    return filas[0] if filas else None


def existe_pelicula(titulo: str, duracion: int) -> bool:
    """Verifica si ya existe una película registrada con ese título y duración."""
    sql = """
          SELECT id
          FROM peliculas
          WHERE titulo = %s AND duracion = %s \
          """
    filas = ejecutar_consulta(sql, (titulo, duracion))
    return len(filas) > 0


def insertar(pelicula: dict) -> int:
    """Guarda una película nueva y devuelve su ID generado."""
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

# guarda tmdb
def actualizar_datos_tmdb(pelicula_id: int, sinopsis: str | None, poster: str | None) -> int:
    sql = """
          UPDATE peliculas
          SET sinopsis = COALESCE(%s, sinopsis),
              poster = COALESCE(%s, poster)
          WHERE id = %s
          """
    return ejecutar_mutacion(sql, (sinopsis, poster, pelicula_id))