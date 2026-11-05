from app.db import ejecutar_consulta, ejecutar_mutacion


def listar() -> list[dict]:
    """Obtiene todos los servicios activos ordenados por ID."""
    sql = """
          SELECT id, nombre, descripcion, precio
          FROM servicios
          WHERE activo = TRUE
          ORDER BY id
          """
    return ejecutar_consulta(sql)


def buscar_por_id(servicio_id: int) -> dict | None:
    """Devuelve el servicio como diccionario, o None si no existe."""
    sql = """
          SELECT id, nombre, descripcion, precio
          FROM servicios
          WHERE id = %s \
          """
    filas = ejecutar_consulta(sql, (servicio_id,))
    return filas[0] if filas else None


def insertar(servicio: dict) -> int:
    """Guarda un servicio nuevo y devuelve su ID generado."""
    sql = """
          INSERT INTO servicios (nombre, descripcion, precio)
          VALUES (%s, %s, %s) \
          """
    parametros = (servicio["nombre"], servicio["descripcion"], servicio["precio"])
    return ejecutar_mutacion(sql, parametros)


def modificar(servicio_id: int, servicio: dict) -> None:
    """Modifica los datos de un servicio existente."""
    sql = """
          UPDATE servicios
          SET nombre = %s, descripcion = %s, precio = %s
          WHERE id = %s \
          """
    parametros = (
        servicio["nombre"],
        servicio["descripcion"],
        servicio["precio"],
        servicio_id,
    )
    ejecutar_mutacion(sql, parametros)


def eliminar(servicio_id: int) -> None:
    """Desactiva el servicio"""
    sql = "UPDATE servicios SET activo = FALSE WHERE id = %s"
    ejecutar_mutacion(sql, (servicio_id,))