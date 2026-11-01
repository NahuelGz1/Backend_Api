import pymysql
from db import obtener_conexion

def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> dict:
    """
    Inserta un nuevo usuario en la base de datos MySQL usando SQL explícito.
    Asigna por defecto el rol 'cliente'.
    """
    conexion = None
    try:
        conexion = obtener_conexion()
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

