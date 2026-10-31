from app.db import ejecutar_consulta

def listar_locales():
    sql = "SELECT DISTINCT local FROM salas ORDER BY local ASC;"
    return ejecutar_consulta(sql)

def listar_salas(local=None):
    sql = "SELECT id, nombre, capacidad, local FROM salas"
    parametros = ()
    if local:
        sql += " WHERE local = %s"
        parametros = (local,)
    sql += " ORDER BY local ASC, nombre ASC;"
    return ejecutar_consulta(sql, parametros)

def listar_funciones():
    sql = """
        SELECT 
            f.id AS funcion_id,
            f.fecha_hora_proyeccion,
            p.id AS pelicula_id, p.titulo AS pelicula_titulo, p.duracion AS pelicula_duracion,
            s.id AS sala_id, s.nombre AS sala_nombre, s.local AS sala_local
        FROM funciones f
        JOIN peliculas p ON p.id = f.id_pelicula
        JOIN salas s ON s.id = f.id_sala
        ORDER BY f.fecha_hora_proyeccion ASC;
    """
    return ejecutar_consulta(sql)

def buscar_funcion_por_id(funcion_id: int):
    sql = """
        SELECT 
            f.id AS funcion_id,
            f.fecha_hora_proyeccion,
            p.id AS pelicula_id, p.titulo AS pelicula_titulo, p.duracion AS pelicula_duracion,
            s.id AS sala_id, s.nombre AS sala_nombre, s.local AS sala_local
        FROM funciones f
        JOIN peliculas p ON p.id = f.id_pelicula
        JOIN salas s ON s.id = f.id_sala
        WHERE f.id = %s;
    """
    filas = ejecutar_consulta(sql, (funcion_id,))
    return filas[0] if filas else None