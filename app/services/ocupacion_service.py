from app.repositories.dashboard_repository import (
    obtener_metricas_ocupacion_por_pelicula,
    obtener_metricas_ocupacion_por_funcion,
    obtener_resumen_general_ocupacion
)
from app.utils.dates import datetime_a_string

def calcular_reporte_ocupacion() -> dict:
    peliculas_db = obtener_metricas_ocupacion_por_pelicula()
    funciones_db = obtener_metricas_ocupacion_por_funcion()
    resumen_db = obtener_resumen_general_ocupacion()

    # Detalle por película con cálculo de porcentaje
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
            "porcentaje_ocupacion": porcentaje
        }
        peliculas_ocupacion.append(item)
        labels_peliculas.append(fila["pelicula_titulo"])
        data_ocupacion_porcentaje.append(porcentaje)

    # Detalle por función individual
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
            "porcentaje_ocupacion": porcentaje
        })

    # Estructura unificada lista para gráficos de barra y torta
    return {
        "resumen_general": {
            "total_entradas_activas": int(resumen_db["total_vendidas"] or 0),
            "total_entradas_canceladas": int(resumen_db["total_canceladas"] or 0),
            # Ideal para gráfico de torta (Pie chart)
            "grafico_torta_estados": {
                "labels": ["Vendidas / Utilizadas", "Canceladas"],
                "data": [
                    int(resumen_db["total_vendidas"] or 0),
                    int(resumen_db["total_canceladas"] or 0)
                ]
            }
        },
        # Ideal para gráfico de barras
        "grafico_barras_peliculas": {
            "labels": labels_peliculas,
            "datasets": [
                {
                    "label": "Porcentaje de Ocupación (%)",
                    "data": data_ocupacion_porcentaje
                }
            ]
        },
        "detalle_peliculas": peliculas_ocupacion,
        "detalle_funciones": funciones_ocupacion
    }