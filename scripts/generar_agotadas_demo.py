"""Crea funciones agotadas de prueba sin modificar funciones o compras existentes."""

from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

from werkzeug.security import generate_password_hash

from app.db import obtener_conexion
from app.utils.constantes import ESTADO_ENTRADA_COMPRADA, PRECIO_ENTRADA_FIJO


PREFIJO_QR = "DEMO-AGOTADA-"
TOTAL_FUNCIONES = 2


def generar_agotadas(ahora=None):
    ahora = ahora or datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    conexion = obtener_conexion()
    creadas = []
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre, local, capacidad FROM salas "
                "WHERE activo = TRUE AND capacidad > 0 ORDER BY local, nombre, id FOR UPDATE"
            )
            salas = cursor.fetchall()
            if not salas:
                raise ValueError("No hay salas activas con capacidad para crear funciones de prueba.")

            cursor.execute(
                """
                SELECT f.id
                FROM funciones f
                JOIN peliculas p ON p.id = f.id_pelicula
                JOIN salas s ON s.id = f.id_sala
                WHERE f.fecha_hora_proyeccion > %s AND f.activo = TRUE
                  AND f.eliminada = FALSE AND f.cancelada = FALSE
                  AND p.activo = TRUE AND p.eliminada = FALSE AND s.activo = TRUE
                  AND EXISTS (
                      SELECT 1 FROM entradas e JOIN compras c ON c.id = e.id_compra
                      WHERE e.id_funcion = f.id AND c.codigo_qr LIKE %s
                  )
                FOR UPDATE
                """,
                (ahora, PREFIJO_QR + "%"),
            )
            faltantes = max(0, TOTAL_FUNCIONES - len(cursor.fetchall()))
            if not faltantes:
                conexion.commit()
                return creadas

            cursor.execute(
                "SELECT p.id, p.titulo, p.duracion FROM peliculas p "
                "WHERE p.activo = TRUE AND p.eliminada = FALSE AND p.duracion > 0 "
                "AND EXISTS (SELECT 1 FROM funciones f WHERE f.id_pelicula = p.id AND f.eliminada = FALSE) "
                "ORDER BY p.id"
            )
            peliculas = cursor.fetchall()
            if not peliculas:
                raise ValueError("No hay películas activas con funciones previas para la demostración.")

            # Priorizamos complejos distintos, sin impedir el uso de una segunda sala del mismo complejo.
            salas_ordenadas = []
            locales = set()
            for sala in salas:
                if sala["local"] not in locales:
                    salas_ordenadas.append(sala)
                    locales.add(sala["local"])
            salas_ordenadas.extend(sala for sala in salas if sala not in salas_ordenadas)

            for sala in salas_ordenadas:
                if len(creadas) >= faltantes:
                    break
                cursor.execute(
                    """
                    SELECT f.fecha_hora_proyeccion, p.duracion
                    FROM funciones f JOIN peliculas p ON p.id = f.id_pelicula
                    WHERE f.id_sala = %s AND f.eliminada = FALSE AND f.cancelada = FALSE
                    FOR UPDATE
                    """,
                    (sala["id"],),
                )
                ocupaciones = [
                    (fila["fecha_hora_proyeccion"],
                     fila["fecha_hora_proyeccion"] + timedelta(minutes=(fila["duracion"] or 0) + 15))
                    for fila in cursor.fetchall()
                ]
                pelicula = peliculas[len(creadas) % len(peliculas)]
                inicio_elegido = None
                for dia in range(3):
                    for minutos in range(10 * 60, 23 * 60 + 1, 30):
                        inicio = datetime.combine(ahora.date() + timedelta(days=dia), time()) + timedelta(minutes=minutos)
                        fin = inicio + timedelta(minutes=pelicula["duracion"] + 15)
                        if inicio > ahora and not any(inicio < fin_ocupado and comienzo < fin
                                                       for comienzo, fin_ocupado in ocupaciones):
                            inicio_elegido = inicio
                            break
                    if inicio_elegido:
                        break
                if inicio_elegido is None:
                    continue

                identificador = uuid4().hex
                qr = PREFIJO_QR + identificador
                cursor.execute(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (%s, %s, %s, %s)",
                    ("Usuario de demostración", f"demo-agotada-{identificador}@example.invalid",
                     generate_password_hash(uuid4().hex), "cliente"),
                )
                usuario_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO funciones (id_pelicula, id_sala, fecha_hora_proyeccion) VALUES (%s, %s, %s)",
                    (pelicula["id"], sala["id"], inicio_elegido),
                )
                funcion_id = cursor.lastrowid
                cursor.execute("INSERT INTO compras (id_usuario, codigo_qr) VALUES (%s, %s)", (usuario_id, qr))
                compra_id = cursor.lastrowid
                cursor.executemany(
                    "INSERT INTO entradas (id_compra, id_funcion, numero_butaca, precio_historico, codigo_qr, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [(compra_id, funcion_id, butaca, PRECIO_ENTRADA_FIJO, qr, ESTADO_ENTRADA_COMPRADA)
                     for butaca in range(1, sala["capacidad"] + 1)],
                )
                creadas.append((funcion_id, inicio_elegido, sala["local"], sala["nombre"], pelicula["titulo"], sala["capacidad"]))

            if len(creadas) < faltantes:
                raise ValueError("No hay suficientes salas y horarios libres para crear las funciones agotadas de prueba.")
        conexion.commit()
        return creadas
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    funciones = generar_agotadas()
    for funcion_id, fecha, local, sala, pelicula, capacidad in funciones:
        print(f"#{funcion_id} | {fecha:%d/%m/%Y %H:%M} | {local} | {sala} | {pelicula} | {capacidad} butacas")
    print(f"Funciones agotadas de prueba creadas: {len(funciones)}")
