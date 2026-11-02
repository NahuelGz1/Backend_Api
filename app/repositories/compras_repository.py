from app.db import ejecutar_consulta, ejecutar_mutacion

def crear_entrada(id_usuario: int, id_funcion: int, numero_butaca: str, codigo_qr: str) -> int:
    sql = """
          INSERT INTO entradas (id_usuario, id_funcion, numero_butaca, codigo_qr, estado)
          VALUES (%s, %s, %s, %s, 'comprada') \
          """
    return ejecutar_mutacion(sql, (id_usuario, id_funcion, numero_butaca, codigo_qr))

def obtener_entrada_por_id(entrada_id: int) -> dict:
    sql = """
          SELECT e.id AS id_entrada, e.id_usuario, e.numero_butaca, e.codigo_qr, e.estado,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula, s.nombre AS sala, s.local
          FROM entradas e
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE e.id = %s \
          """
    resultado = ejecutar_consulta(sql, (entrada_id,))
    return resultado[0] if resultado else None

def actualizar_estado_entrada(entrada_id: int, nuevo_estado: str) -> int:
    sql = "UPDATE entradas SET estado = %s WHERE id = %s"
    return ejecutar_mutacion(sql, (nuevo_estado, entrada_id))

def verificar_butaca_ocupada(id_funcion: int, numero_butaca: str) -> bool:
    sql = """
          SELECT id FROM entradas
          WHERE id_funcion = %s AND numero_butaca = %s AND estado != 'cancelada' \
          """
    resultado = ejecutar_consulta(sql, (id_funcion, numero_butaca))
    return len(resultado) > 0