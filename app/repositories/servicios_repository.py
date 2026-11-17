from app.db import ejecutar_consulta, ejecutar_mutacion


def listar(incluir_inactivos: bool = False) -> list[dict]:
    """Obtiene servicios, ocultando las bajas salvo que se solicite lo contrario."""
    sql = """
          SELECT id, nombre, descripcion, precio, categoria, activo, imagen_url
          FROM servicios
          """
    if not incluir_inactivos:
        sql += " WHERE activo = TRUE"
    sql += " ORDER BY id"
    return ejecutar_consulta(sql)


def buscar_por_id(servicio_id: int) -> dict | None:
    """Devuelve el servicio como diccionario, o None si no existe."""
    sql = """
          SELECT id, nombre, descripcion, precio, categoria, activo, imagen_url
          FROM servicios
          WHERE id = %s \
          """
    filas = ejecutar_consulta(sql, (servicio_id,))
    return filas[0] if filas else None


def insertar(servicio: dict) -> int:
    """Guarda un servicio nuevo y devuelve su ID generado."""
    sql = """
          INSERT INTO servicios (nombre, descripcion, precio, categoria, imagen_url)
          VALUES (%s, %s, %s, %s, %s) \
          """
    parametros = (
        servicio["nombre"], servicio["descripcion"], servicio["precio"],
        servicio["categoria"], servicio["imagen_url"],
    )
    return ejecutar_mutacion(sql, parametros)


def modificar(servicio_id: int, servicio: dict) -> None:
    """Modifica los datos de un servicio existente."""
    sql = """
          UPDATE servicios
          SET nombre = %s, descripcion = %s, precio = %s, categoria = %s,
              imagen_url = COALESCE(%s, imagen_url)
          WHERE id = %s \
          """
    parametros = (
        servicio["nombre"],
        servicio["descripcion"],
        servicio["precio"],
        servicio["categoria"],
        servicio["imagen_url"],
        servicio_id,
    )
    ejecutar_mutacion(sql, parametros)


def eliminar(servicio_id: int) -> None:
    """Elimina el servicio del catálogo."""
    sql = "DELETE FROM servicios WHERE id = %s"
    ejecutar_mutacion(sql, (servicio_id,))


def cambiar_estado(servicio_id: int, activo: bool) -> None:
    ejecutar_mutacion(
        "UPDATE servicios SET activo = %s WHERE id = %s",
        (activo, servicio_id),
    )