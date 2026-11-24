from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion
from app.utils.constantes import (
    ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_CANCELADA, ESTADO_ENTRADA_UTILIZADA,
    LIMITE_ESTACIONAMIENTO_POR_FUNCION,
)
from app.validators.compra_validator import validar_cupo_estacionamiento


def obtener_disponibilidad_estacionamiento(id_funcion: int, cursor=None) -> dict:
    """Cuenta cada detalle una vez mientras su compra tenga entradas activas en la función."""
    sql = """
          SELECT COALESCE(SUM(ds.cantidad), 0) AS vendidos
          FROM detalles_servicios ds
          JOIN servicios s ON s.id = ds.id_servicio
          WHERE LOWER(s.nombre) LIKE %s
            AND EXISTS (
                SELECT 1 FROM entradas e
                WHERE e.id_compra = ds.id_compra AND e.id_funcion = %s
                  AND e.estado IN (%s, %s)
            )
          """
    parametros = ("%estacionamiento%", id_funcion, ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_UTILIZADA)
    if cursor is None:
        vendidos = int(ejecutar_consulta(sql, parametros)[0]["vendidos"])
    else:
        cursor.execute(sql, parametros)
        vendidos = int(cursor.fetchone()["vendidos"])
    return {
        "limite": LIMITE_ESTACIONAMIENTO_POR_FUNCION,
        "vendidos": vendidos,
        "disponibles": max(0, LIMITE_ESTACIONAMIENTO_POR_FUNCION - vendidos),
    }


def guardar_compra_completa(
    id_usuario: int, codigo_qr: str, entradas_data: list,
    servicios_data: list = None, *, validar_funcion,
) -> int:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            ids_funciones = {entrada["id_funcion"] for entrada in entradas_data}
            if len(ids_funciones) != 1:
                raise ValueError("La compra debe contener entradas de una sola función.", 400)
            id_funcion = next(iter(ids_funciones))
            cursor.execute(
                """
                SELECT f.fecha_hora_proyeccion, f.activo, f.eliminada, f.cancelada,
                       p.activo AS pelicula_activa, p.eliminada AS pelicula_eliminada
                FROM funciones f
                JOIN peliculas p ON p.id = f.id_pelicula
                WHERE f.id = %s FOR UPDATE
                """,
                (id_funcion,),
            )
            funcion = cursor.fetchone()
            validar_funcion(funcion)

            numeros = [entrada["numero_butaca"] for entrada in entradas_data]
            cursor.execute(
                """
                SELECT numero_butaca FROM entradas
                WHERE id_funcion = %s AND numero_butaca IN %s AND estado != %s
                FOR UPDATE
                """,
                (id_funcion, numeros, ESTADO_ENTRADA_CANCELADA),
            )
            conflictos = sorted(fila["numero_butaca"] for fila in cursor.fetchall())
            if conflictos:
                raise ValueError(f"Las butacas {conflictos} ya se encuentran ocupadas.", 409)

            catalogo = {}
            if servicios_data:
                for id_servicio in sorted({serv["id_servicio"] for serv in servicios_data}):
                    cursor.execute(
                        "SELECT nombre, precio, activo FROM servicios WHERE id = %s FOR UPDATE",
                        (id_servicio,),
                    )
                    servicio = cursor.fetchone()
                    if not servicio or not servicio["activo"]:
                        raise ValueError("Un servicio ya no está disponible. Revisá tu compra.", 409)
                    catalogo[id_servicio] = servicio
                for serv in servicios_data:
                    if serv["precio"] != catalogo[serv["id_servicio"]]["precio"]:
                        raise ValueError("El precio de un servicio cambió. Revisá tu compra antes de confirmar.", 409)
                cantidad = sum(
                    serv["cantidad"] for serv in servicios_data
                    if "estacionamiento" in catalogo[serv["id_servicio"]]["nombre"].lower()
                )
                if cantidad:
                    disponibilidad = obtener_disponibilidad_estacionamiento(id_funcion, cursor)
                    validar_cupo_estacionamiento(cantidad, len(entradas_data), disponibilidad["disponibles"])

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
                    cursor.execute(sql_servicio, (
                        id_compra, serv["id_servicio"], serv["cantidad"],
                        catalogo[serv["id_servicio"]]["precio"],
                    ))

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
    cabecera = ejecutar_consulta(
        "SELECT id, id_usuario, codigo_qr, fecha_hora FROM compras WHERE id = %s",
        (compra_id,),
    )
    if not cabecera:
        return None
    sql = """
          SELECT e.id AS id_entrada, e.id_funcion,
                 e.numero_butaca, e.precio_historico, e.codigo_qr,
                 e.estado, f.fecha_hora_proyeccion, p.titulo AS pelicula,
                 p.poster, s.nombre AS sala, s.local
          FROM entradas e
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE e.id_compra = %s
          ORDER BY e.numero_butaca
          """
    entradas = ejecutar_consulta(sql, (compra_id,))
    return {
        "compra": cabecera[0],
        "entradas": entradas,
        "servicios": obtener_servicios_por_compra(compra_id),
    }


def obtener_entradas_por_qr(codigo_qr: str) -> list[dict]:
    sql = """
          SELECT e.id AS id_entrada, c.id_usuario, c.id AS id_compra,
                 e.numero_butaca, e.codigo_qr, e.estado,
                 u.nombre AS nombre_usuario, u.email AS email_usuario,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula, f.id_pelicula,
                 s.nombre AS sala, s.local, e.precio_historico
          FROM entradas e
                   JOIN compras c ON e.id_compra = c.id
                   JOIN usuarios u ON c.id_usuario = u.id
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
          SELECT ds.id AS id_detalle, s.id AS id_servicio, s.nombre, s.categoria, ds.cantidad, ds.usado,
                 ds.cantidad_usada, ds.precio_historico AS precio
          FROM detalles_servicios ds
                   JOIN servicios s ON ds.id_servicio = s.id
          WHERE ds.id_compra = %s
          ORDER BY ds.id
          """
    return ejecutar_consulta(sql, (id_compra,))


def obtener_compra_por_qr(codigo_qr: str) -> dict | None:
    resultado = ejecutar_consulta(
        "SELECT id, id_usuario, codigo_qr FROM compras WHERE codigo_qr = %s", (codigo_qr,)
    )
    return resultado[0] if resultado else None


def canjear_entrada(id_compra: int, id_entrada: int) -> bool:
    sql = """
          UPDATE entradas
          SET estado = %s
          WHERE id = %s AND id_compra = %s AND estado = %s
          """
    return _canjear_con_compra_bloqueada(
        id_compra, sql, (ESTADO_ENTRADA_UTILIZADA, id_entrada, id_compra, ESTADO_ENTRADA_COMPRADA)
    )


def canjear_unidad_servicio(id_compra: int, id_detalle: int) -> bool:
    # usado se asigna antes que cantidad_usada: MySQL evalúa las asignaciones de izquierda a derecha
    sql = """
          UPDATE detalles_servicios
          SET usado = (cantidad_usada + 1 >= cantidad), cantidad_usada = cantidad_usada + 1
          WHERE id = %s AND id_compra = %s AND cantidad_usada < cantidad
          """
    return _canjear_con_compra_bloqueada(id_compra, sql, (id_detalle, id_compra))


def _canjear_con_compra_bloqueada(id_compra: int, sql: str, parametros: tuple) -> bool:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM compras WHERE id = %s FOR UPDATE", (id_compra,))
            if not cursor.fetchone():
                conexion.rollback()
                return False
            cursor.execute(
                "SELECT estado FROM entradas WHERE id_compra = %s FOR UPDATE",
                (id_compra,),
            )
            entradas = cursor.fetchall()
            if not any(e["estado"] != ESTADO_ENTRADA_CANCELADA for e in entradas):
                conexion.rollback()
                return False
            cursor.execute(sql, parametros)
            afectadas = cursor.rowcount
        conexion.commit()
        return afectadas > 0
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


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
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id FROM compras WHERE id = %s FOR UPDATE", (id_compra,))
            if not cursor.fetchone():
                conexion.rollback()
                return 0
            cursor.execute("SELECT estado FROM entradas WHERE id_compra = %s FOR UPDATE", (id_compra,))
            entradas = cursor.fetchall()
            if any(e["estado"] not in (ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_CANCELADA) for e in entradas):
                raise ValueError("No se puede cancelar una compra con entradas utilizadas.")
            cursor.execute(
                "SELECT cantidad_usada, usado FROM detalles_servicios WHERE id_compra = %s FOR UPDATE",
                (id_compra,),
            )
            if any(s["cantidad_usada"] or s["usado"] for s in cursor.fetchall()):
                raise ValueError("No se puede cancelar una compra con servicios utilizados.")
            cursor.execute(
                "UPDATE entradas SET estado = %s WHERE id_compra = %s AND estado = %s",
                (ESTADO_ENTRADA_CANCELADA, id_compra, ESTADO_ENTRADA_COMPRADA),
            )
            afectadas = cursor.rowcount
        conexion.commit()
        return afectadas
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_resena_actualizar(id_usuario: int, id_pelicula: int, puntuacion: int) -> int:
    sql = """
    INSERT INTO reseñas (id_usuario, id_pelicula, puntuacion)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE puntuacion = VALUES(puntuacion)
    """
    return ejecutar_mutacion(sql, (id_usuario, id_pelicula, puntuacion))


def usuario_asistio_a_pelicula(id_usuario: int, id_pelicula: int) -> bool:
    sql = """
    SELECT 1
    FROM compras c
    JOIN entradas e ON c.id = e.id_compra
    JOIN funciones f ON e.id_funcion = f.id
    WHERE c.id_usuario = %s
      AND f.id_pelicula = %s
      AND e.estado = %s
    LIMIT 1
    """
    resultado = ejecutar_consulta(sql, (id_usuario, id_pelicula, ESTADO_ENTRADA_UTILIZADA))
    return len(resultado) > 0


def ver_puntuaciones(id_pelicula: int) -> dict:
    sql = """
    SELECT
        COALESCE(ROUND(AVG(puntuacion), 0), 0) AS promedio,
        COUNT(*) AS total
    FROM reseñas
    WHERE id_pelicula = %s
    """
    resultado = ejecutar_consulta(sql, (id_pelicula,))
    if resultado and resultado[0]:
        return {
            "promedio": int(resultado[0]["promedio"] or 0),
            "total": int(resultado[0]["total"] or 0)
        }
    return {"promedio": 0, "total": 0}


def agregar_servicios_a_compra(
    id_compra: int, id_usuario: int, servicios_data: list, *, validar_funcion,
) -> int:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id, id_usuario FROM compras WHERE id = %s FOR UPDATE",
                (id_compra,),
            )
            compra = cursor.fetchone()
            if not compra:
                raise ValueError("La compra seleccionada no existe.", 404)
            if int(compra["id_usuario"]) != int(id_usuario):
                raise PermissionError("No tenés permiso para modificar esta compra.")

            cursor.execute(
                """
                SELECT id_funcion, estado FROM entradas
                WHERE id_compra = %s FOR UPDATE
                """,
                (id_compra,),
            )
            entradas = cursor.fetchall()
            activas = [e for e in entradas if e["estado"] == ESTADO_ENTRADA_COMPRADA]
            if not activas:
                raise ValueError("La compra no tiene entradas activas disponibles para adjuntar servicios.", 409)

            id_funcion = activas[0]["id_funcion"]
            cursor.execute(
                """
                SELECT f.fecha_hora_proyeccion, f.activo, f.eliminada, f.cancelada,
                       p.activo AS pelicula_activa, p.eliminada AS pelicula_eliminada
                FROM funciones f
                JOIN peliculas p ON p.id = f.id_pelicula
                WHERE f.id = %s FOR UPDATE
                """,
                (id_funcion,),
            )
            validar_funcion(cursor.fetchone())

            # Servicios ya comprados previamente en esta misma compra (para respetar topes por entrada)
            cursor.execute(
                """
                SELECT ds.cantidad, s.nombre
                FROM detalles_servicios ds
                JOIN servicios s ON s.id = ds.id_servicio
                WHERE ds.id_compra = %s FOR UPDATE
                """,
                (id_compra,),
            )
            previos = cursor.fetchall()
            estacionamiento_previo = sum(
                int(p["cantidad"]) for p in previos if "estacionamiento" in p["nombre"].lower()
            )
            vip_previo = sum(
                int(p["cantidad"]) for p in previos if "vip" in p["nombre"].lower()
            )

            catalogo = {}
            for id_servicio in sorted({serv["id_servicio"] for serv in servicios_data}):
                cursor.execute(
                    "SELECT nombre, precio, activo FROM servicios WHERE id = %s FOR UPDATE",
                    (id_servicio,),
                )
                servicio = cursor.fetchone()
                if not servicio or not servicio["activo"]:
                    raise ValueError("Un servicio ya no está disponible. Revisá tu compra.", 409)
                catalogo[id_servicio] = servicio

            estacionamiento_nuevo = 0
            vip_nuevo = 0
            for serv in servicios_data:
                if serv["precio"] != catalogo[serv["id_servicio"]]["precio"]:
                    raise ValueError("El precio de un servicio cambió. Revisá tu compra antes de confirmar.", 409)
                nombre_serv = catalogo[serv["id_servicio"]]["nombre"].lower()
                if "estacionamiento" in nombre_serv:
                    estacionamiento_nuevo += serv["cantidad"]
                elif "vip" in nombre_serv:
                    vip_nuevo += serv["cantidad"]

            if vip_previo + vip_nuevo > len(activas):
                raise ValueError("La cantidad total de accesos VIP no puede superar la cantidad de entradas.", 400)

            if estacionamiento_nuevo:
                disponibilidad = obtener_disponibilidad_estacionamiento(id_funcion, cursor)
                validar_cupo_estacionamiento(
                    estacionamiento_previo + estacionamiento_nuevo,
                    len(activas),
                    disponibilidad["disponibles"] + estacionamiento_previo,
                )

            for serv in servicios_data:
                precio_actual = catalogo[serv["id_servicio"]]["precio"]
                cursor.execute(
                    """
                    SELECT id FROM detalles_servicios
                    WHERE id_compra = %s AND id_servicio = %s AND precio_historico = %s
                    ORDER BY id ASC LIMIT 1
                    FOR UPDATE
                    """,
                    (id_compra, serv["id_servicio"], precio_actual),
                )
                existente = cursor.fetchone()
                if existente:
                    cursor.execute(
                        """
                        UPDATE detalles_servicios
                        SET usado = (cantidad_usada >= cantidad + %s),
                            cantidad = cantidad + %s
                        WHERE id = %s
                        """,
                        (serv["cantidad"], serv["cantidad"], existente["id"]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO detalles_servicios (id_compra, id_servicio, cantidad, precio_historico)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (id_compra, serv["id_servicio"], serv["cantidad"], precio_actual),
                    )

            conexion.commit()
            return id_compra
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def guardar_compra_solo_servicios(id_usuario: int, codigo_qr: str, servicios_data: list) -> int:
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            catalogo = {}
            for id_servicio in sorted({serv["id_servicio"] for serv in servicios_data}):
                cursor.execute(
                    "SELECT nombre, precio, activo FROM servicios WHERE id = %s FOR UPDATE",
                    (id_servicio,),
                )
                servicio = cursor.fetchone()
                if not servicio or not servicio["activo"]:
                    raise ValueError("Un servicio ya no está disponible. Revisá tu compra.", 409)
                nombre_norm = servicio["nombre"].lower()
                if "estacionamiento" in nombre_norm or "vip" in nombre_norm:
                    raise ValueError("Estacionamiento y Acceso VIP requieren una entrada asociada.", 400)
                catalogo[id_servicio] = servicio

            for serv in servicios_data:
                if serv["precio"] != catalogo[serv["id_servicio"]]["precio"]:
                    raise ValueError("El precio de un servicio cambió. Revisá tu compra antes de confirmar.", 409)

            cursor.execute(
                "INSERT INTO compras (id_usuario, codigo_qr) VALUES (%s, %s)",
                (id_usuario, codigo_qr),
            )
            id_compra = cursor.lastrowid

            sql_servicio = """
                           INSERT INTO detalles_servicios (id_compra, id_servicio, cantidad, precio_historico)
                           VALUES (%s, %s, %s, %s)
                           """
            for serv in servicios_data:
                cursor.execute(sql_servicio, (
                    id_compra, serv["id_servicio"], serv["cantidad"],
                    catalogo[serv["id_servicio"]]["precio"],
                ))

            conexion.commit()
            return id_compra
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()