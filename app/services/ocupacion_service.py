from app.db import ejecutar_consulta
from decimal import Decimal
from app.repositories.dashboard_repository import (
    obtener_metricas_ocupacion_por_funcion,
    obtener_metricas_ocupacion_por_pelicula,
    obtener_resumen_general_ocupacion,
    obtener_ventas_por_genero,
    obtener_ventas_por_franja_horaria,
    obtener_metricas_servicios_por_pelicula,
    obtener_servicios_vendidos,
    obtener_periodos_ocupacion,
)
from app.utils.dates import datetime_a_string
from app.services.funciones_service import verificar_funcion_vigente


def _desglose_servicios(servicios):
    grupos = {
        "candy_bar": {"ingresos": Decimal("0"), "unidades": 0},
        "mejoras_experiencia": {"ingresos": Decimal("0"), "unidades": 0},
        "otras_categorias": {"ingresos": Decimal("0"), "unidades": 0},
    }
    for servicio in servicios:
        categoria = servicio["categoria"]
        if categoria in ("Bebidas", "Pochoclos", "Snacks"):
            grupo = grupos["candy_bar"]
        elif categoria == "Mejoras de experiencia":
            grupo = grupos["mejoras_experiencia"]
        else:
            grupo = grupos["otras_categorias"]
        grupo["ingresos"] += Decimal(str(servicio["ingresos"]))
        grupo["unidades"] += int(servicio["cantidad"])
    return {
        nombre: {"ingresos": float(grupo["ingresos"]), "unidades": grupo["unidades"]}
        for nombre, grupo in grupos.items()
    }


def calcular_reporte_ocupacion(complejo=None, periodo=None) -> dict:
    peliculas_db = obtener_metricas_ocupacion_por_pelicula(complejo, periodo)
    funciones_db = obtener_metricas_ocupacion_por_funcion(complejo, periodo)
    resumen_db = obtener_resumen_general_ocupacion(complejo, periodo)
    generos_db = obtener_ventas_por_genero(complejo, periodo)
    franjas_db = obtener_ventas_por_franja_horaria(complejo, periodo)
    servicios_db = {
        fila["id_pelicula"]: fila
        for fila in obtener_metricas_servicios_por_pelicula(complejo, periodo)
    }
    servicios_pelicula = {}
    for fila in obtener_servicios_vendidos(complejo, periodo):
        servicios_pelicula.setdefault(fila["id_pelicula"], []).append(fila)
    servicios_generales = _desglose_servicios(obtener_servicios_vendidos(complejo, periodo, por_pelicula=False))
    ingresos_generales = sum(Decimal(str(grupo["ingresos"])) for grupo in servicios_generales.values())
    periodos = [
        f'{fila["anio"]:04d}-{fila["mes"]:02d}'
        for fila in obtener_periodos_ocupacion(complejo)
    ]

    resumen_general = {
        "total_vendidas": int(resumen_db.get("total_vendidas", 0)),
        "total_canceladas": int(resumen_db.get("total_canceladas", 0)),
        "total_generadas": int(resumen_db.get("total_generadas", 0)),
        "total_ingresos": float(resumen_db.get("total_ingresos", 0.0)),
        "ingresos_servicios": float(ingresos_generales),
        "desglose_servicios": servicios_generales,
    }

    por_pelicula = []
    for fila in peliculas_db:
        servicios = servicios_db.get(fila["id_pelicula"], {})
        compras_activas = int(servicios.get("compras_activas", 0))
        compras_con_servicios = int(servicios.get("compras_con_servicios", 0))
        ingresos_servicios = Decimal(str(servicios.get("ingresos_servicios", 0)))
        ingresos_entradas = Decimal(str(fila.get("total_ingresos", 0)))
        productos = servicios_pelicula.get(fila["id_pelicula"], [])
        candy = next((producto for producto in productos if producto["categoria"] in ("Bebidas", "Pochoclos", "Snacks")), None)
        top = productos[0] if productos else None
        por_pelicula.append({
            "id_pelicula": fila["id_pelicula"],
            "pelicula_titulo": fila["pelicula_titulo"],
            "genero": fila.get("genero", ""),
            "total_funciones": int(fila.get("total_funciones", 0)),
            "capacidad_total_ofertada": int(fila.get("capacidad_total_ofertada", 0)),
            "total_entradas_vendidas": int(fila.get("total_entradas_vendidas", 0)),
            "total_entradas_canceladas": int(fila.get("total_entradas_canceladas", 0)),
            "total_ingresos": float(ingresos_entradas),
            "ingresos_servicios": float(ingresos_servicios),
            "compras_con_servicios": compras_con_servicios,
            "tasa_servicios": round(compras_con_servicios / compras_activas * 100, 1) if compras_activas else 0,
            "servicio_mas_vendido": {"nombre": top["nombre"], "cantidad": int(top["cantidad"])} if top else None,
            "desglose_servicios": _desglose_servicios(productos),
            "candy_mas_vendido": {"nombre": candy["nombre"], "cantidad": int(candy["cantidad"])} if candy else None,
            "mejoras_vendidas": [
                {"nombre": producto["nombre"], "cantidad": int(producto["cantidad"])}
                for producto in productos if producto["categoria"] == "Mejoras de experiencia"
            ],
            "ingresos_totales_combinados": float(ingresos_entradas + ingresos_servicios),
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

    cancelaciones_por_funcion = []
    for fila in obtener_metricas_ocupacion_por_funcion(complejo, periodo, incluir_eliminadas=True):
        canceladas = int(fila.get("butacas_canceladas", 0))
        if not canceladas:
            continue
        emitidas = int(fila["butacas_ocupadas"]) + canceladas
        cancelaciones_por_funcion.append({
            "id_funcion": fila["id_funcion"],
            "pelicula_titulo": fila["pelicula_titulo"],
            "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
            "cine_local": fila["cine_local"],
            "sala_nombre": fila["sala_nombre"],
            "entradas_canceladas": canceladas,
            "entradas_emitidas": emitidas,
            "tasa_cancelacion": round(canceladas / emitidas * 100, 1),
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
        "cancelaciones_por_funcion": cancelaciones_por_funcion,
        "por_genero": por_genero,
        "por_franja_horaria": por_franja_horaria,
        "periodos_disponibles": periodos,
    }


def obtener_estado_butacas(funcion_id: int) -> list:
    # solo se muestra el mapa de funciones que siguen a la venta
    funcion = verificar_funcion_vigente(funcion_id)
    capacidad = int(funcion["sala_capacidad"])

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