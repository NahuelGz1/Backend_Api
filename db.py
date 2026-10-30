import os
from pymysql import connect
from pymysql.cursors import DictCursor

def obtener_conexion():
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=DictCursor,
            autocommit=False
        )
        return connection
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def ejecutar_consulta(sql: str, parametros: tuple = ()) -> list[dict]:
    """
    Ejecuta consultas de lectura (SELECT) y devuelve una lista de diccionarios.
    Ejemplo: ejecutar_consulta("SELECT * FROM peliculas WHERE id = %s", (1,))
    """
    conexion = obtener_conexion()
    if not conexion:
        return []

    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()


def ejecutar_mutacion(sql: str, parametros: tuple = ()) -> int:
    """
    Ejecuta consultas de escritura (INSERT, UPDATE, DELETE).
    Maneja el commit y rollback automáticamente.
    Retorna el ID autogenerado (lastrowid) o la cantidad de filas afectadas.
    """
    conexion = obtener_conexion()
    if not conexion:
        return 0

    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            conexion.commit()
            # Si fue un INSERT devuelve el ID generado; si fue UPDATE/DELETE devuelve las filas afectadas
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Exception as e:
        conexion.rollback()
        print(f"Error en la transacción SQL: {e}")
        return 0
    finally:
        conexion.close()