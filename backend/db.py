import os
from dotenv import load_dotenv
from pymysql import connect

load_dotenv()

def obtener_conexion():
    """Establece y devuelve una conexión con la base de datos MySQL"""
    connection = connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )
    return connection
