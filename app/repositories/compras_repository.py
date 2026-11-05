from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion
from app.utils.constantes import ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_CANCELADA

def guardar_compra_completa(id_usuario: int, entradas_data: list, servicios_data: list = None) -> int:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("INSERT INTO compras (id_usuario) VALUES (%s)", (id_usuario,))
            id_compra = cursor.lastrowid

            sql_entrada = """
                          INSERT INTO entradas (id_compra, id_funcion, numero_butaca, precio_historico, codigo_qr, estado)
                          VALUES (%s, %s, %s, %s, %s, %s) \
                          """
            for ent in entradas_data:
                cursor.execute(sql_entrada, (id_compra, ent['id_funcion'], ent['numero_butaca'], ent['precio'], ent['qr'], ESTADO_ENTRADA_COMPRADA))

            if servicios_data:
                sql_servicio = """
                               INSERT INTO detalles_servicios (id_compra, id_servicio, cantidad, precio_historico)
                               VALUES (%s, %s, %s, %s) \
                               """
                for serv in servicios_data:
                    cursor.execute(sql_servicio, (id_compra, serv['id_servicio'], serv['cantidad'], serv['precio']))

            conexion.commit()
            return id_compra
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def obtener_entrada_por_id(entrada_id: int) -> dict | None:
    sql = """
          SELECT e.id AS id_entrada, c.id_usuario, e.numero_butaca, e.codigo_qr, e.estado,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula, s.nombre AS sala, s.local, e.precio_historico
          FROM entradas e
                   JOIN compras c ON e.id_compra = c.id
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE e.id = %s
          """
    resultado = ejecutar_consulta(sql, (entrada_id,))
    return resultado[0] if resultado else None


def obtener_entrada_por_qr(codigo_qr: str) -> dict | None:
    sql = """
          SELECT e.id AS id_entrada, c.id_usuario, e.numero_butaca, e.codigo_qr, e.estado,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula, s.nombre AS sala, e.precio_historico
          FROM entradas e
                   JOIN compras c ON e.id_compra = c.id
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE e.codigo_qr = %s
          """
    resultado = ejecutar_consulta(sql, (codigo_qr,))
    return resultado[0] if resultado else None


def actualizar_estado_entrada(entrada_id: int, nuevo_estado: str) -> int:
    sql = "UPDATE entradas SET estado = %s WHERE id = %s"
    return ejecutar_mutacion(sql, (nuevo_estado, entrada_id))


def verificar_butaca_ocupada(id_funcion: int, numero_butaca: str) -> bool:
    sql = """
          SELECT id FROM entradas
          WHERE id_funcion = %s AND numero_butaca = %s AND estado != %s
          """
    resultado = ejecutar_consulta(sql, (id_funcion, numero_butaca, ESTADO_ENTRADA_CANCELADA))
    return len(resultado) > 0

def obtener_servicios_por_compra(id_compra: int) -> list:
    sql = """
          SELECT ds.id AS id_detalle, s.nombre, ds.cantidad, ds.usado
          FROM detalles_servicios ds
                   JOIN servicios s ON ds.id_servicio = s.id
          WHERE ds.id_compra = %s \
          """
    return ejecutar_consulta(sql, (id_compra,))


def marcar_servicio_usado(id_detalle: int) -> bool:
    sql = "UPDATE detalles_servicios SET usado = TRUE WHERE id = %s AND usado = FALSE"
    filas_afectadas = ejecutar_comando(sql, (id_detalle,))
    return filas_afectadas > 0