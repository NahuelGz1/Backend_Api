from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion
from app.utils.constantes import ESTADO_ENTRADA_CANCELADA, ESTADO_ENTRADA_COMPRADA


def listar_locales() -> list[dict]:
    sql = """
          SELECT DISTINCT local
          FROM salas
          ORDER BY local ASC;
          """
    return ejecutar_consulta(sql)


def listar_salas(local: str | None = None) -> list[dict]:
    sql = """
          SELECT id, nombre, capacidad, local, activo
          FROM salas
          """
    parametros = []
    if local:
        sql += " WHERE local = %s"
        parametros.append(local)

    sql += " ORDER BY local ASC, nombre ASC;"
    return ejecutar_consulta(sql, tuple(parametros))


# columnas comunes de una funcion, con la capacidad de la sala y las entradas activas
SELECT_FUNCION = """
          SELECT
              f.id AS funcion_id,
              f.fecha_hora_proyeccion,
              f.activo,
              f.eliminada,
              f.cancelada,
              f.motivo_cancelacion,
              p.id AS pelicula_id,
              p.titulo AS pelicula_titulo,
              p.poster AS pelicula_poster,
              p.duracion AS pelicula_duracion,
              p.activo AS pelicula_activa,
              p.eliminada AS pelicula_eliminada,
              s.id AS sala_id,
              s.nombre AS sala_nombre,
              s.local AS sala_local,
              s.capacidad AS sala_capacidad,
              s.activo AS sala_activa,
              (
                  SELECT COUNT(*)
                  FROM entradas e
                  WHERE e.id_funcion = f.id AND e.estado != %s
              ) AS entradas_activas
          FROM funciones f
                   JOIN peliculas p ON p.id = f.id_pelicula
                   JOIN salas s ON s.id = f.id_sala
          """


def listar_funciones(incluir_inactivas: bool = False, desde=None) -> list[dict]:
    sql = SELECT_FUNCION + " WHERE f.eliminada = FALSE"
    parametros = [ESTADO_ENTRADA_CANCELADA]
    if not incluir_inactivas:
        sql += " AND f.activo = TRUE AND p.activo = TRUE AND p.eliminada = FALSE AND s.activo = TRUE"
    if desde is not None:
        sql += " AND f.fecha_hora_proyeccion > %s"
        parametros.append(desde)
    sql += " ORDER BY f.fecha_hora_proyeccion ASC"
    return ejecutar_consulta(sql, tuple(parametros))


def buscar_funcion_por_id(funcion_id: int) -> dict | None:
    sql = SELECT_FUNCION + " WHERE f.id = %s;"
    filas = ejecutar_consulta(sql, (ESTADO_ENTRADA_CANCELADA, funcion_id))
    return filas[0] if filas else None


def buscar_sala_por_id(sala_id: int) -> dict | None:
    sql = """
          SELECT id, nombre, capacidad, local, activo
          FROM salas
          WHERE id = %s;
          """
    filas = ejecutar_consulta(sql, (sala_id,))
    return filas[0] if filas else None


def listar_funciones_de_sala(sala_id: int) -> list[dict]:
    sql = """
          SELECT
              f.id AS funcion_id,
              f.fecha_hora_proyeccion,
              p.titulo AS pelicula_titulo,
              p.duracion AS pelicula_duracion
          FROM funciones f
                   JOIN peliculas p ON p.id = f.id_pelicula
          WHERE f.id_sala = %s AND f.eliminada = FALSE AND f.cancelada = FALSE
          ORDER BY f.fecha_hora_proyeccion ASC;
          """
    return ejecutar_consulta(sql, (sala_id,))


def obtener_butacas_ocupadas(id_funcion: int) -> list:
    sql = """
          SELECT numero_butaca FROM entradas
          WHERE id_funcion = %s AND estado != %s;
          """
    resultado = ejecutar_consulta(sql, (id_funcion, ESTADO_ENTRADA_CANCELADA))
    return [item["numero_butaca"] for item in resultado]


def contar_entradas_de_funcion(funcion_id: int) -> dict:
    sql = """
          SELECT
              COUNT(*) AS total,
              COALESCE(SUM(CASE WHEN estado IN ('comprada', 'utilizada') THEN 1 ELSE 0 END), 0) AS activas
          FROM entradas
          WHERE id_funcion = %s;
          """
    filas = ejecutar_consulta(sql, (funcion_id,))
    return filas[0]


def insertar_funcion(id_pelicula: int, id_sala: int, fecha_hora_proyeccion) -> int:
    sql = """
          INSERT INTO funciones (id_pelicula, id_sala, fecha_hora_proyeccion)
          VALUES (%s, %s, %s);
          """
    return ejecutar_mutacion(sql, (id_pelicula, id_sala, fecha_hora_proyeccion))


def actualizar_funcion(funcion_id: int, id_pelicula: int, id_sala: int, fecha_hora_proyeccion) -> None:
    sql = """
          UPDATE funciones
          SET id_pelicula = %s, id_sala = %s, fecha_hora_proyeccion = %s
          WHERE id = %s;
          """
    ejecutar_mutacion(sql, (id_pelicula, id_sala, fecha_hora_proyeccion, funcion_id))


def eliminar_funcion(funcion_id: int) -> None:
    sql = "UPDATE funciones SET activo = FALSE, eliminada = TRUE WHERE id = %s;"
    ejecutar_mutacion(sql, (funcion_id,))


def cambiar_estado_funcion(funcion_id: int, activo: bool) -> None:
    ejecutar_mutacion(
        "UPDATE funciones SET activo = %s WHERE id = %s",
        (activo, funcion_id),
    )


def cancelar_funcion(funcion_id: int, motivo: str) -> list[dict]:
    # en una sola transaccion: marca la funcion, toma las entradas vendidas y las cancela
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE funciones
                SET activo = FALSE, cancelada = TRUE, motivo_cancelacion = %s
                WHERE id = %s AND cancelada = FALSE
                """,
                (motivo, funcion_id),
            )
            cursor.execute(
                """
                SELECT e.id AS id_entrada, e.id_compra, e.numero_butaca, e.precio_historico,
                       c.codigo_qr, u.id AS id_usuario, u.nombre, u.email
                FROM entradas e
                         JOIN compras c ON c.id = e.id_compra
                         JOIN usuarios u ON u.id = c.id_usuario
                WHERE e.id_funcion = %s AND e.estado = %s
                ORDER BY e.id_compra, e.numero_butaca
                """,
                (funcion_id, ESTADO_ENTRADA_COMPRADA),
            )
            entradas = cursor.fetchall()
            cursor.execute(
                "UPDATE entradas SET estado = %s WHERE id_funcion = %s AND estado = %s",
                (ESTADO_ENTRADA_CANCELADA, funcion_id, ESTADO_ENTRADA_COMPRADA),
            )
            conexion.commit()
            return list(entradas)
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
