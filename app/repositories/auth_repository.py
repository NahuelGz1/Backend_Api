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
import pymysql
from db import obtener_conexion, ejecutar_consulta

def buscar_por_email(email: str) -> dict | None:
    """
    Busca un usuario por su email.
    Retorna el diccionario con sus datos (id, nombre, email, password_hash, rol) o None si no existe.
    """
    query = "SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE email = %s"
    resultados = ejecutar_consulta(query, (email,))
    return resultados[0] if resultados else None

def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> dict:
    """
    Inserta un nuevo usuario en la base de datos MySQL usando SQL explícito.
    Asigna por defecto el rol 'cliente'.
    """
    conexion = None
    try:
        conexion = obtener_conexion()
        if not conexion:
            return {"error": "No se pudo conectar con la base de datos MySQL. Verifica que el servicio esté activo y las credenciales en .env sean correctas."}

        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO usuarios (nombre, email, password_hash, rol)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, email, password_hash, rol))
            conexion.commit()
            
            nuevo_id = cursor.lastrowid
            return {
                "id": nuevo_id,
                "nombre": nombre,
                "email": email,
                "rol": rol
            }
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            return {"error": "El correo electrónico ya se encuentra registrado"}
        return {"error": f"Error de integridad en la base de datos: {str(e)}"}
    except pymysql.err.OperationalError as e:
        return {"error": f"No se pudo conectar con MySQL: {str(e)}"}
    finally:
        if conexion:
            conexion.close()

