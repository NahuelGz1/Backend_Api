from app.db import *

def obtener_usuario_por_id(id_usuario: int):
    query = """
            SELECT id, nombre, email, rol
            FROM usuarios
            WHERE id = %s 
            """
    resultados = ejecutar_consulta(query, (id_usuario,))
    return resultados[0] if resultados else None


def obtener_historial_servicios_por_usuario(id_usuario: int):
    query = """
            SELECT
                compras_servicios.id AS id_compra_servicio,
                compras_servicios.fecha_hora_compra,
                servicios.id AS id_servicio,
                servicios.nombre,
                servicios.precio
            FROM compras_servicios
                     INNER JOIN servicios ON compras_servicios.id_servicio = servicios.id
            WHERE compras_servicios.id_usuario = %s
            ORDER BY compras_servicios.fecha_hora_compra DESC 
            """
    return ejecutar_consulta(query, (id_usuario,))


def obtener_historial_entradas_por_usuario(id_usuario: int):
    """
    Obtiene el listado de entradas compradas por el usuario con el detalle
    de la película, la sala, el horario de la función y la butaca.
    """
    query = """
            SELECT
                entradas.id AS id_entrada,
                entradas.numero_butaca,
                entradas.codigo_qr,
                entradas.estado,
                funciones.id AS id_funcion,
                funciones.fecha_hora_proyeccion,
                peliculas.titulo,
                peliculas.poster,
                peliculas.duracion ,
                salas.nombre ,
                salas.local 
            FROM entradas
                     INNER JOIN funciones ON entradas.id_funcion = funciones.id
                     INNER JOIN peliculas ON funciones.id_pelicula = peliculas.id
                     INNER JOIN salas ON funciones.id_sala = salas.id
            WHERE entradas.id_usuario = %s
            ORDER BY funciones.fecha_hora_proyeccion DESC 
            """
    return ejecutar_consulta(query, (id_usuario,))

