from db import obtener_conexion


def consultar_butacas(funcion_id):
    """
    Obtiene la capacidad de la sala y las butacas ocupadas
    correspondientes a una función.
    """
    conexion = obtener_conexion()

    try:
        with conexion.cursor() as cursor:

            # Obtener la capacidad de la sala
            cursor.execute("""
                SELECT s.capacidad
                FROM funciones AS f
                JOIN salas AS s ON f.id_sala = s.id
                WHERE f.id = %s
            """, (funcion_id,))

            funcion = cursor.fetchone()

            if funcion is None:
                return None

            # Obtener las butacas ocupadas
            cursor.execute("""
                SELECT numero_butaca
                FROM entradas
                WHERE id_funcion = %s
                AND estado IN ('comprada', 'utilizada')
            """, (funcion_id,))

            resultados = cursor.fetchall()

            ocupadas = []

            for fila in resultados:
                ocupadas.append(fila["numero_butaca"])

            return {
                "capacidad": funcion["capacidad"],
                "ocupadas": ocupadas
            }

    finally:
        conexion.close()