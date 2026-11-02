from app.db import ejecutar_consulta, ejecutar_mutacion


def listar():
    #Todos los servicios
    sql = """
          SELECT id, nombre, descripcion, precio
          FROM servicios
          ORDER BY id
          """
    return ejecutar_consulta(sql, ())


def buscar_por_id(servicio_id):
    #Devuelve el servicio como diccionario, o None si no existe
    sql = """
          SELECT id, nombre, descripcion, precio
          FROM servicios
          WHERE id = %s
          """
    filas = ejecutar_consulta(sql, (servicio_id,))

    if len(filas) > 0:
        return filas[0]
    else:
        return None


def insertar(servicio):
    #Guarda un servicio nuevo y devuelve su id
    sql = """
          INSERT INTO servicios (nombre, descripcion, precio)
          VALUES (%s, %s, %s)
          """
    parametros = (servicio["nombre"], servicio["descripcion"], servicio["precio"])
    return ejecutar_mutacion(sql, parametros)


def modificar(servicio_id, servicio):
    #Cambia los datos de un servicio
    sql = """
          UPDATE servicios
          SET nombre = %s, descripcion = %s, precio = %s
          WHERE id = %s
          """
    parametros = (servicio["nombre"], servicio["descripcion"], servicio["precio"], servicio_id)
    ejecutar_mutacion(sql, parametros)


def eliminar(servicio_id):
    #Borra un servicio
    sql = "DELETE FROM servicios WHERE id = %s"
    ejecutar_mutacion(sql, (servicio_id,))