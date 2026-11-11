from app.db import ejecutar_consulta
from app.repositories.dashboard_repository import (
    obtener_metricas_ocupacion_por_funcion,
    obtener_metricas_ocupacion_por_pelicula,
    obtener_resumen_general_ocupacion,
    obtener_ventas_por_genero,
    obtener_ventas_por_franja_horaria
)
from app.utils.dates import datetime_a_string


def calcular_reporte_ocupacion(complejo=None) -> dict:
    peliculas_db = obtener_metricas_ocupacion_por_pelicula()
    funciones_db = obtener_metricas_ocupacion_por_funcion(complejo)
    resumen_db = obtener_resumen_general_ocupacion(complejo)
    if complejo:
        ids = {f.get("pelicula_titulo") for f in funciones_db}
        peliculas_db = [p for p in peliculas_db if p.get("pelicula_titulo") in ids]
    generos_db = obtener_ventas_por_genero(complejo)
    franjas_db = obtener_ventas_por_franja_horaria(complejo)

    resumen_general = {
        "total_vendidas": int(resumen_db.get("total_vendidas", 0)),
        "total_canceladas": int(resumen_db.get("total_canceladas", 0)),
        "total_generadas": int(resumen_db.get("total_generadas", 0)),
        "total_ingresos": float(resumen_db.get("total_ingresos", 0.0))
    }

    por_pelicula = []
    for fila in peliculas_db:
        por_pelicula.append({
            "id_pelicula": fila["id_pelicula"],
            "pelicula_titulo": fila["pelicula_titulo"],
            "genero": fila.get("genero", ""),
            "total_funciones": int(fila.get("total_funciones", 0)),
            "capacidad_total_ofertada": int(fila.get("capacidad_total_ofertada", 0)),
            "total_entradas_vendidas": int(fila.get("total_entradas_vendidas", 0)),
            "total_entradas_canceladas": int(fila.get("total_entradas_canceladas", 0)),
            "total_ingresos": float(fila.get("total_ingresos", 0.0))
        })

    por_funcion = []
    for fila in funciones_db:
        por_funcion.append({
            "id_funcion": fila["id_funcion"],
            "pelicula_titulo": fila["pelicula_titulo"],
            "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
            "cine_local": fila["cine_local"],
            "sala_nombre": fila["sala_nombre"],
            "sala_capacidad": int(fila["sala_capacidad"]),
            "butacas_ocupadas": int(fila["butacas_ocupadas"]),
            "butacas_canceladas": int(fila.get("butacas_canceladas", 0)),
            "butacas_libres": int(fila.get("butacas_libres", 0)),
            "total_ingresos": float(fila.get("total_ingresos", 0.0))
        })

    por_genero = [
        {
            "genero": fila["genero"],
            "total_entradas": int(fila["total_entradas"]),
            "total_ingresos": float(fila.get("total_ingresos", 0.0))
        } for fila in generos_db
    ]

    por_franja_horaria = [
        {
            "hora": int(fila["hora"]),
            "total_entradas": int(fila["total_entradas"]),
            "total_ingresos": float(fila.get("total_ingresos", 0.0))
        } for fila in franjas_db
    ]

    return {
        "resumen_general": resumen_general,
        "por_pelicula": por_pelicula,
        "por_funcion": por_funcion,
        "por_genero": por_genero,
        "por_franja_horaria": por_franja_horaria
    }


def obtener_estado_butacas(funcion_id: int) -> list:
    sql_sala = """
               SELECT s.capacidad
               FROM funciones f
                        JOIN salas s ON f.id_sala = s.id
               WHERE f.id = %s \
               """
    sala = ejecutar_consulta(sql_sala, (funcion_id,))
    if not sala:
        raise ValueError("La función solicitada no existe.")

    capacidad = sala[0]["capacidad"]

    sql_ocupadas = """
                   SELECT numero_butaca
                   FROM entradas
                   WHERE id_funcion = %s AND estado != 'cancelada' \
                   """
    ocupadas_bd = ejecutar_consulta(sql_ocupadas, (funcion_id,))

    butacas_ocupadas = {fila["numero_butaca"] for fila in ocupadas_bd}

    disponibilidad = []
    for i in range(1, capacidad + 1):
        disponibilidad.append({
            "numero_butaca": i,
            "estado": "ocupada" if i in butacas_ocupadas else "disponible",
        })

    return disponibilidad