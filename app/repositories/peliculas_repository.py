from datetime import datetime, timedelta, timezone
from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion
from app.utils.constantes import ESTADO_ENTRADA_CANCELADA


def _ahora() -> datetime:
    """Devuelve la hora actual de Argentina (UTC-3) como datetime sin zona horaria."""
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _sql_funciones_vigentes(solo_una_pelicula: bool = False) -> str:
    """Arma la consulta SQL para obtener funciones vigentes."""
    sql = """
          SELECT funciones.id, funciones.id_pelicula, funciones.fecha_hora_proyeccion,
                 salas.nombre AS sala, salas.local, salas.capacidad,
                 (
                     SELECT COUNT(*)
                     FROM entradas
                     WHERE entradas.id_funcion = funciones.id AND entradas.estado != '{cancelada}'
                 ) AS entradas_activas
          FROM funciones
                   JOIN salas ON salas.id = funciones.id_sala
          WHERE funciones.activo = TRUE
            AND salas.activo = TRUE
            AND funciones.eliminada = FALSE
            AND funciones.cancelada = FALSE
            AND funciones.fecha_hora_proyeccion > %s \
          """.format(cancelada=ESTADO_ENTRADA_CANCELADA)
    if solo_una_pelicula:
        sql += " AND funciones.id_pelicula = %s"

    return sql + " ORDER BY funciones.fecha_hora_proyeccion"


def listar_peliculas_en_cartelera() -> list[dict]:
    """Películas que tienen al menos una función vigente."""
    sql = """
          SELECT peliculas.id, peliculas.titulo, peliculas.sinopsis, peliculas.poster, peliculas.duracion,
                 peliculas.clasificacion, peliculas.genero, peliculas.activo, peliculas.eliminada,
                 (destacada.id_pelicula IS NOT NULL) AS destacada
          FROM peliculas
          LEFT JOIN pelicula_destacada destacada ON destacada.id = 1 AND destacada.id_pelicula = peliculas.id
          WHERE peliculas.activo = TRUE AND peliculas.eliminada = FALSE AND EXISTS (
              SELECT 1
              FROM funciones
              WHERE funciones.id_pelicula = peliculas.id
                AND funciones.activo = TRUE
                AND funciones.eliminada = FALSE
                AND funciones.cancelada = FALSE
                AND EXISTS (SELECT 1 FROM salas WHERE salas.id = funciones.id_sala AND salas.activo = TRUE)
                AND funciones.fecha_hora_proyeccion > %s
          )
          ORDER BY peliculas.titulo \
          """
    return ejecutar_consulta(sql, (_ahora(),))


def listar_estrenos() -> list[dict]:
    """Películas activas que no tienen ninguna función asignada."""
    sql = """
          SELECT peliculas.id, peliculas.titulo, peliculas.sinopsis, peliculas.poster, peliculas.duracion,
                 peliculas.clasificacion, peliculas.genero, peliculas.activo, peliculas.eliminada
          FROM peliculas
          WHERE peliculas.activo = TRUE AND peliculas.eliminada = FALSE AND NOT EXISTS (
              SELECT 1
              FROM funciones
              WHERE funciones.id_pelicula = peliculas.id
                AND funciones.eliminada = FALSE
          )
          ORDER BY peliculas.titulo \
          """
    return ejecutar_consulta(sql)


def listar_todas() -> list[dict]:
    return ejecutar_consulta(
        """
        SELECT id, titulo, sinopsis, poster, duracion, clasificacion, genero, activo, eliminada
        FROM peliculas
        WHERE eliminada = FALSE
        ORDER BY titulo
        """
    )


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
          SELECT id, titulo, sinopsis, poster, duracion, clasificacion, genero, activo, eliminada
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
          INSERT INTO peliculas (titulo, sinopsis, poster, duracion, clasificacion, genero, activo, eliminada)
          VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE) \
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


def actualizar(pelicula_id: int, cambios: dict, ahora) -> None:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, titulo, duracion, eliminada FROM peliculas WHERE id = %s FOR UPDATE", (pelicula_id,))
            actual = cursor.fetchone()
            if not actual or actual["eliminada"]:
                raise ValueError("Película no encontrada", 404)
            titulo = cambios.get("titulo", actual["titulo"])
            duracion = cambios.get("duracion", actual["duracion"])
            cursor.execute(
                "SELECT id FROM peliculas WHERE titulo = %s AND duracion = %s AND id != %s LIMIT 1",
                (titulo, duracion, pelicula_id),
            )
            if cursor.fetchone():
                raise ValueError("Ya existe una película con ese título y esa duración", 409)
            if duracion != actual["duracion"]:
                cursor.execute(
                    """
                    SELECT 1 FROM funciones
                    WHERE id_pelicula = %s AND eliminada = FALSE AND cancelada = FALSE
                      AND DATE_ADD(fecha_hora_proyeccion, INTERVAL (COALESCE(%s, 0) + 15) MINUTE) > %s
                    LIMIT 1
                    """,
                    (pelicula_id, actual["duracion"], ahora),
                )
                if cursor.fetchone():
                    raise ValueError("No se puede cambiar la duración mientras haya funciones futuras o en curso. Cancelalas o esperá a que terminen.", 409)
            campos = ("titulo", "sinopsis", "poster", "duracion", "clasificacion", "genero", "activo")
            seleccionados = [campo for campo in campos if campo in cambios]
            cursor.execute(
                "UPDATE peliculas SET " + ", ".join(f"{campo} = %s" for campo in seleccionados) + " WHERE id = %s",
                tuple(cambios[campo] for campo in seleccionados) + (pelicula_id,),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

# guarda tmdb
def actualizar_datos_tmdb(pelicula_id: int, sinopsis: str | None, poster: str | None) -> int:
    sql = """
          UPDATE peliculas
          SET sinopsis = COALESCE(NULLIF(sinopsis, ''), %s),
              poster = COALESCE(NULLIF(poster, ''), %s)
          WHERE id = %s
          """
    return ejecutar_mutacion(sql, (sinopsis, poster, pelicula_id))


def cambiar_estado(pelicula_id: int, activo: bool) -> int:
    return ejecutar_mutacion(
        "UPDATE peliculas SET activo = %s WHERE id = %s",
        (activo, pelicula_id),
    )


def eliminar(pelicula_id: int) -> int:
    return ejecutar_mutacion(
        "UPDATE peliculas SET activo = FALSE, eliminada = TRUE WHERE id = %s",
        (pelicula_id,),
    )
