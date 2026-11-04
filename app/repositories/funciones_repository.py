from app.db import ejecutar_consulta, ejecutar_mutacion
from app.utils.constantes import ESTADO_ENTRADA_CANCELADA


def listar_locales() -> list[dict]:
    sql = """
          SELECT DISTINCT local
          FROM salas
          ORDER BY local ASC;
          """
    return ejecutar_consulta(sql)


def listar_salas(local: str | None = None) -> list[dict]:
    sql = """
          SELECT id, nombre, capacidad, local
          FROM salas
          """
    parametros = []
    if local:
        sql += " WHERE local = %s"
        parametros.append(local)

    sql += " ORDER BY local ASC, nombre ASC;"
    return ejecutar_consulta(sql, tuple(parametros))


def listar_funciones() -> list[dict]:
    sql = """
          SELECT
              f.id AS funcion_id,
              f.fecha_hora_proyeccion,
              p.id AS pelicula_id,
              p.titulo AS pelicula_titulo,
              p.duracion AS pelicula_duracion,
              s.id AS sala_id,
              s.nombre AS sala_nombre,
              s.local AS sala_local
          FROM funciones f
                   JOIN peliculas p ON p.id = f.id_pelicula
                   JOIN salas s ON s.id = f.id_sala
          ORDER BY f.fecha_hora_proyeccion ASC;
          """
    return ejecutar_consulta(sql)


def buscar_funcion_por_id(funcion_id: int) -> dict | None:
    sql = """
          SELECT
              f.id AS funcion_id,
              f.fecha_hora_proyeccion,
              p.id AS pelicula_id,
              p.titulo AS pelicula_titulo,
              p.duracion AS pelicula_duracion,
              s.id AS sala_id,
              s.nombre AS sala_nombre,
              s.local AS sala_local
          FROM funciones f
                   JOIN peliculas p ON p.id = f.id_pelicula
                   JOIN salas s ON s.id = f.id_sala
          WHERE f.id = %s;
          """
    filas = ejecutar_consulta(sql, (funcion_id,))
    return filas[0] if filas else None


def buscar_sala_por_id(sala_id: int) -> dict | None:
    sql = """
          SELECT id, nombre, capacidad, local
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
          WHERE f.id_sala = %s
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
    sql = "DELETE FROM funciones WHERE id = %s;"
    ejecutar_mutacion(sql, (funcion_id,))