from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion
from app.utils.constantes import ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_CANCELADA

def guardar_compra_completa(id_usuario: int, codigo_qr: str, entradas_data: list, servicios_data: list = None) -> int:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO compras (id_usuario, codigo_qr) VALUES (%s, %s)",
                (id_usuario, codigo_qr),
            )
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
          SELECT e.id AS id_entrada, c.id_usuario, c.codigo_qr, e.numero_butaca, e.estado,
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


def obtener_compra_completa(compra_id: int) -> dict | None:
    sql = """
          SELECT c.id AS id_compra, c.id_usuario, c.codigo_qr AS codigo_compra,
                 c.fecha_hora, e.id AS id_entrada, e.id_funcion,
                 e.numero_butaca, e.precio_historico, e.codigo_qr,
                 e.estado, f.fecha_hora_proyeccion, p.titulo AS pelicula,
                 p.poster, s.nombre AS sala, s.local
          FROM compras c
                   JOIN entradas e ON e.id_compra = c.id
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE c.id = %s
          ORDER BY e.numero_butaca
          """
    entradas = ejecutar_consulta(sql, (compra_id,))
    if not entradas:
        return None
    return {
        "compra": {
            "id": entradas[0]["id_compra"],
            "id_usuario": entradas[0]["id_usuario"],
            "codigo_qr": entradas[0]["codigo_compra"],
            "fecha_hora": entradas[0]["fecha_hora"],
        },
        "entradas": entradas,
        "servicios": obtener_servicios_por_compra(compra_id),
    }


def obtener_entradas_por_qr(codigo_qr: str) -> list[dict]:
    sql = """
          SELECT e.id AS id_entrada, c.id_usuario, c.id AS id_compra,
                 e.numero_butaca, e.codigo_qr, e.estado,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula,
                 s.nombre AS sala, s.local, e.precio_historico
          FROM entradas e
                   JOIN compras c ON e.id_compra = c.id
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE c.codigo_qr = %s
          """
    return ejecutar_consulta(sql, (codigo_qr,))


def actualizar_estado_entrada(entrada_id: int, nuevo_estado: str) -> int:
    sql = "UPDATE entradas SET estado = %s WHERE id = %s"
    return ejecutar_mutacion(sql, (nuevo_estado, entrada_id))


def actualizar_estado_entradas_de_compra(id_compra: int, estado_actual: str, nuevo_estado: str) -> int:
    sql = """
          UPDATE entradas
          SET estado = %s
          WHERE id_compra = %s AND estado = %s
          """
    return ejecutar_mutacion(sql, (nuevo_estado, id_compra, estado_actual))


def verificar_butaca_ocupada(id_funcion: int, numero_butaca: str) -> bool:
    sql = """
          SELECT id FROM entradas
          WHERE id_funcion = %s AND numero_butaca = %s AND estado != %s
          """
    resultado = ejecutar_consulta(sql, (id_funcion, numero_butaca, ESTADO_ENTRADA_CANCELADA))
    return len(resultado) > 0

def obtener_servicios_por_compra(id_compra: int) -> list:
    sql = """
          SELECT ds.id AS id_detalle, s.nombre, ds.cantidad, ds.usado,
                 ds.precio_historico AS precio
          FROM detalles_servicios ds
                   JOIN servicios s ON ds.id_servicio = s.id
          WHERE ds.id_compra = %s \
          """
    return ejecutar_consulta(sql, (id_compra,))


def marcar_servicio_usado(id_detalle: int) -> bool:
    sql = "UPDATE detalles_servicios SET usado = TRUE WHERE id = %s AND usado = FALSE"
    filas_afectadas = ejecutar_mutacion(sql, (id_detalle,))
    return filas_afectadas > 0

#función para validar las 2 horas
def obtener_datos_resumen_compra(id_compra: int) -> dict | None:
    sql = """
          SELECT c.id_usuario, MIN(f.fecha_hora_proyeccion) as fecha_proyeccion
          FROM compras c
                   JOIN entradas e ON c.id = e.id_compra
                   JOIN funciones f ON e.id_funcion = f.id
          WHERE c.id = %s
          GROUP BY c.id_usuario
          """
    resultado = ejecutar_consulta(sql, (id_compra,))
    return resultado[0] if resultado else None


def cancelar_entradas_por_compra(id_compra: int) -> int:
    sql = "UPDATE entradas SET estado = %s WHERE id_compra = %s AND estado = %s"
    return ejecutar_mutacion(sql, (ESTADO_ENTRADA_CANCELADA, id_compra, ESTADO_ENTRADA_COMPRADA))