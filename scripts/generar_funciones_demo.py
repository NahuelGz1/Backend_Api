"""Genera funciones de demostración sin modificar funciones existentes."""

from datetime import datetime, time, timedelta, timezone

from app.db import obtener_conexion


def generar_funciones(ahora=None, ids_peliculas_demo=()):
    ahora = ahora or datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    conexion = obtener_conexion()
    creadas = []
    try:
        with conexion.cursor() as cursor:
            condicion_demo = ""
            parametros = ()
            if ids_peliculas_demo:
                condicion_demo = " OR p.id IN %s"
                parametros = (tuple(ids_peliculas_demo),)
            cursor.execute(
                "SELECT p.id, p.titulo, p.duracion FROM peliculas p "
                "WHERE p.activo = TRUE AND p.eliminada = FALSE AND p.duracion > 0 "
                "AND (EXISTS (SELECT 1 FROM funciones f WHERE f.id_pelicula = p.id AND f.eliminada = FALSE)"
                + condicion_demo + ") ORDER BY p.id",
                parametros,
            )
            peliculas = cursor.fetchall()
            if not peliculas:
                raise ValueError("No hay películas activas con duración y funciones previas para programar. Los próximos estrenos se conservan sin funciones.")

            cursor.execute("SELECT id, nombre, local FROM salas WHERE activo = TRUE ORDER BY local, nombre, id")
            salas = cursor.fetchall()
            if not salas:
                raise ValueError("No hay salas activas para programar.")

            for indice_sala, sala in enumerate(salas):
                cursor.execute("SELECT activo FROM salas WHERE id = %s FOR UPDATE", (sala["id"],))
                sala_actual = cursor.fetchone()
                if not sala_actual or not sala_actual["activo"]:
                    raise ValueError(f"La sala {sala['nombre']} de {sala['local']} ya no está disponible.")
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
                for dia in range(3):
                    for turno, hora in enumerate((14, 17, 20, 23)):
                        inicio = datetime.combine(ahora.date() + timedelta(days=dia), time(hora))
                        if inicio <= ahora:
                            continue
                        pelicula = peliculas[(dia * len(salas) * 4 + indice_sala * 4 + turno) % len(peliculas)]
                        fin = inicio + timedelta(minutes=pelicula["duracion"] + 15)
                        if any(inicio < ocupado_fin and ocupado_inicio < fin
                               for ocupado_inicio, ocupado_fin in ocupaciones):
                            continue
                        cursor.execute(
                            "INSERT INTO funciones (id_pelicula, id_sala, fecha_hora_proyeccion) VALUES (%s, %s, %s)",
                            (pelicula["id"], sala["id"], inicio),
                        )
                        ocupaciones.append((inicio, fin))
                        creadas.append((inicio, sala["local"], sala["nombre"], pelicula["titulo"]))
        conexion.commit()
        return creadas
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    funciones = generar_funciones()
    for fecha, local, sala, pelicula in funciones:
        print(f"{fecha:%d/%m/%Y %H:%M} | {local} | {sala} | {pelicula}")
    print(f"Funciones creadas: {len(funciones)}")
