from app.db import ejecutar_consulta, ejecutar_mutacion


def listar_salas(local=None):
    sql = """
          SELECT id, nombre, capacidad, local, activo
          FROM salas \
          """

    parametros = []

    if local:
        sql += " WHERE local = %s"
        parametros.append(local)

    sql += " ORDER BY local ASC, nombre ASC"

    return ejecutar_consulta(sql, tuple(parametros))


def buscar_por_id(sala_id):
    sql = """
          SELECT id, nombre, capacidad, local, activo
          FROM salas
          WHERE id = %s \
          """

    filas = ejecutar_consulta(sql, (sala_id,))
    return filas[0] if filas else None


def actualizar(sala_id, nombre, capacidad, local):
    sql = """
          UPDATE salas
          SET nombre = %s,
              capacidad = %s,
              local = %s
          WHERE id = %s \
          """

    ejecutar_mutacion(
        sql,
        (nombre, capacidad, local, sala_id),
    )


def crear(nombre, capacidad, local):
    sql = """
          INSERT INTO salas (nombre, capacidad, local)
          VALUES (%s, %s, %s) \
          """

    return ejecutar_mutacion(
        sql,
        (nombre, capacidad, local),
    )


def cambiar_estado(sala_id, activo):
    ejecutar_mutacion("UPDATE salas SET activo = %s WHERE id = %s", (activo, sala_id))
