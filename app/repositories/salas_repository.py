from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion


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


def actualizar(sala_id, nombre, capacidad, local, activo, ahora):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, nombre, capacidad, local, activo FROM salas WHERE id = %s FOR UPDATE", (sala_id,))
            actual = cursor.fetchone()
            if not actual:
                raise ValueError(f"No existe la sala {sala_id}")

            nombre = actual["nombre"] if nombre is None else nombre
            capacidad = actual["capacidad"] if capacidad is None else capacidad
            local = actual["local"] if local is None else local
            if activo is False and actual["activo"]:
                cursor.execute(
                    """
                    SELECT 1 FROM funciones f
                    JOIN peliculas p ON p.id = f.id_pelicula
                    WHERE f.id_sala = %s
                      AND DATE_ADD(f.fecha_hora_proyeccion, INTERVAL (COALESCE(p.duracion, 0) + 15) MINUTE) > %s
                      AND f.activo = TRUE AND f.eliminada = FALSE AND f.cancelada = FALSE
                    LIMIT 1
                    """,
                    (sala_id, ahora),
                )
                if cursor.fetchone():
                    raise ValueError("No se puede poner la sala en mantenimiento mientras tenga funciones activas en curso o futuras. Desactivá o cancelá las funciones futuras y esperá a que terminen las funciones en curso.")
            if (nombre, capacidad, local) != (actual["nombre"], actual["capacidad"], actual["local"]):
                cursor.execute(
                    """
                    SELECT 1 FROM entradas e
                    JOIN funciones f ON f.id = e.id_funcion
                    WHERE f.id_sala = %s AND f.fecha_hora_proyeccion > %s
                      AND f.cancelada = FALSE AND e.estado != 'cancelada'
                    LIMIT 1
                    """,
                    (sala_id, ahora),
                )
                if cursor.fetchone():
                    raise ValueError("No se puede modificar la configuración de una sala con entradas vendidas para funciones futuras.")

            cursor.execute(
                "UPDATE salas SET nombre = %s, capacidad = %s, local = %s, activo = %s WHERE id = %s",
                (nombre, capacidad, local, actual["activo"] if activo is None else activo, sala_id),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear(nombre, capacidad, local):
    sql = """
          INSERT INTO salas (nombre, capacidad, local)
          VALUES (%s, %s, %s) \
          """

    return ejecutar_mutacion(
        sql,
        (nombre, capacidad, local),
    )
