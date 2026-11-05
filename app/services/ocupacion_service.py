from app.db import ejecutar_consulta
from app.repositories.dashboard_repository import (
    obtener_metricas_ocupacion_por_funcion,
    obtener_metricas_ocupacion_por_pelicula,
    obtener_resumen_general_ocupacion,
    obtener_ventas_por_genero,
    obtener_ventas_por_franja_horaria
)
from app.utils.dates import datetime_a_string


def calcular_reporte_ocupacion() -> dict:
    peliculas_db = obtener_metricas_ocupacion_por_pelicula()
    funciones_db = obtener_metricas_ocupacion_por_funcion()
    resumen_db = obtener_resumen_general_ocupacion()

    generos_db = obtener_ventas_por_genero()
    franjas_db = obtener_ventas_por_franja_horaria()

    #detalle por película con cálculo de porcentaje
    peliculas_ocupacion = []
    labels_peliculas = []
    data_ocupacion_porcentaje = []

    for fila in peliculas_db:
        capacidad = int(fila["capacidad_total_ofertada"])
        vendidas = int(fila["total_entradas_vendidas"])
        porcentaje = round((vendidas / capacidad * 100), 2) if capacidad > 0 else 0.0

        item = {
            "id_pelicula": fila["id_pelicula"],
            "pelicula": fila["pelicula_titulo"],
            "genero": fila["genero"],
            "total_funciones": int(fila["total_funciones"]),
            "capacidad_total": capacidad,
            "entradas_vendidas": vendidas,
            "entradas_canceladas": int(fila["total_entradas_canceladas"]),
            "porcentaje_ocupacion": porcentaje,
        }
        peliculas_ocupacion.append(item)
        labels_peliculas.append(fila["pelicula_titulo"])
        data_ocupacion_porcentaje.append(porcentaje)

    # detalle por función individual
    funciones_ocupacion = []
    for fila in funciones_db:
        capacidad = int(fila["sala_capacidad"])
        ocupadas = int(fila["butacas_ocupadas"])
        porcentaje = round((ocupadas / capacidad * 100), 2) if capacidad > 0 else 0.0

        funciones_ocupacion.append({
            "id_funcion": fila["id_funcion"],
            "fecha_hora": datetime_a_string(fila["fecha_hora_proyeccion"]),
            "pelicula": fila["pelicula_titulo"],
            "sala": fila["sala_nombre"],
            "local": fila["cine_local"],
            "capacidad": capacidad,
            "butacas_ocupadas": ocupadas,
            "butacas_libres": int(fila["butacas_libres"]),
            "porcentaje_ocupacion": porcentaje,
        })

    #estructura unificada lista para gráficos
    return {
        "resumen_general": {
            "total_entradas_activas": int(resumen_db.get("total_vendidas", 0)),
            "total_entradas_canceladas": int(resumen_db.get("total_canceladas", 0)),
            "grafico_torta_estados": {
                "labels": ["Vendidas / Utilizadas", "Canceladas"],
                "data": [
                    int(resumen_db.get("total_vendidas", 0)),
                    int(resumen_db.get("total_canceladas", 0)),
                ],
            },
        },
        "grafico_barras_peliculas": {
            "labels": labels_peliculas,
            "datasets": [
                {
                    "label": "Porcentaje de Ocupación (%)",
                    "data": data_ocupacion_porcentaje,
                }
            ],
        },
        "grafico_torta_generos": {
            "labels": [fila["genero"] for fila in generos_db],
            "data": [fila["total_entradas"] for fila in generos_db]
        },
        "grafico_barras_horarios": {
            "labels": [f"{fila['hora']}:00" for fila in franjas_db],
            "data": [fila["total_entradas"] for fila in franjas_db]
        },
        "detalle_peliculas": peliculas_ocupacion,
        "detalle_funciones": funciones_ocupacion,
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