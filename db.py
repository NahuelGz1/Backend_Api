import os
import pymysql
from pymysql.cursors import DictCursor

def obtener_conexion():
    """
    Crea y devuelve la conexión a la base de datos usando las variables de entorno.
    Si falla, lanza la excepción para ser capturada por el handler global.
    """
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "cine_db"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=DictCursor,
        autocommit=False
    )

def ejecutar_consulta(sql: str, parametros: tuple = ()) -> list[dict]:
    """
    Ejecuta consultas SELECT y devuelve una lista de diccionarios.
    Lanza la excepción si ocurre un error en la base de datos.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()

def ejecutar_mutacion(sql: str, parametros: tuple = ()) -> int:
    """
    Ejecuta consultas INSERT, UPDATE o DELETE con manejo explícito de transacciones.
    En caso de error hace rollback y vuelve a lanzar la excepción.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            conexion.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()