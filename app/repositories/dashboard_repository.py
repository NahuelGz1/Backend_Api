from app.db import ejecutar_consulta


def _filtros_funcion(local=None, periodo=None, alias_funcion="f", alias_sala="s"):
    filtros = []
    parametros = []
    if local:
        filtros.append(f"{alias_sala}.local = %s")
        parametros.append(local)
    if periodo:
        filtros.append(f"{alias_funcion}.fecha_hora_proyeccion >= %s")
        filtros.append(f"{alias_funcion}.fecha_hora_proyeccion < %s")
        parametros.extend(periodo)
    return filtros, parametros


def obtener_metricas_ocupacion_por_pelicula(local=None, periodo=None) -> list[dict]:
    """
    Calcula por película:
    - Entradas vendidas (compradas o utilizadas)
    - Entradas canceladas
    - Capacidad total ofertada (sin contar las funciones eliminadas)
    - Total recaudado en dinero (total_ingresos)
    """
    filtros, parametros = _filtros_funcion(local, periodo)
    condiciones = " AND ".join(filtros)
    query = """
            SELECT
                p.id AS id_pelicula,
                p.titulo AS pelicula_titulo,
                p.genero,
                COUNT(CASE WHEN f.eliminada = FALSE THEN f.id END) AS total_funciones,
                COALESCE(SUM(CASE WHEN f.eliminada = FALSE THEN s.capacidad ELSE 0 END), 0) AS capacidad_total_ofertada,
                COALESCE(SUM(e.vendidas), 0) AS total_entradas_vendidas,
                COALESCE(SUM(e.canceladas), 0) AS total_entradas_canceladas,
                COALESCE(SUM(e.ingresos), 0) AS total_ingresos
            FROM peliculas p
                     LEFT JOIN funciones f ON p.id = f.id_pelicula
                     LEFT JOIN salas s ON f.id_sala = s.id
                     LEFT JOIN (
                         SELECT id_funcion,
                                SUM(CASE WHEN estado IN ('comprada', 'utilizada') THEN 1 ELSE 0 END) AS vendidas,
                                SUM(CASE WHEN estado = 'cancelada' THEN 1 ELSE 0 END) AS canceladas,
                                SUM(CASE WHEN estado IN ('comprada', 'utilizada') THEN precio_historico ELSE 0 END) AS ingresos
                         FROM entradas GROUP BY id_funcion
                     ) e ON f.id = e.id_funcion
            {where}
            GROUP BY p.id, p.titulo, p.genero
            ORDER BY total_entradas_vendidas DESC
            """
    return ejecutar_consulta(query.format(where=f"WHERE {condiciones}" if condiciones else ""), tuple(parametros) or None)


def obtener_metricas_servicios_por_pelicula(local=None, periodo=None) -> list[dict]:
    filtros, parametros = _filtros_funcion(local, periodo)
    condiciones = " AND ".join(["e.estado IN ('comprada', 'utilizada')"] + filtros)
    compras_activas = """
        SELECT DISTINCT f.id_pelicula, e.id_compra
        FROM entradas e
        INNER JOIN funciones f ON f.id = e.id_funcion
        INNER JOIN salas s ON s.id = f.id_sala
        WHERE {condiciones}
    """.format(condiciones=condiciones)
    query = """
        SELECT activas.id_pelicula, COUNT(DISTINCT activas.id_compra) AS compras_activas,
               COUNT(DISTINCT ds.id_compra) AS compras_con_servicios,
               COALESCE(SUM(ds.cantidad * ds.precio_historico), 0) AS ingresos_servicios
        FROM ({compras_activas}) activas
        LEFT JOIN detalles_servicios ds ON ds.id_compra = activas.id_compra AND ds.cantidad > 0
        GROUP BY activas.id_pelicula
    """.format(compras_activas=compras_activas)
    return ejecutar_consulta(query, tuple(parametros) or None)


def obtener_servicios_vendidos(local=None, periodo=None, por_pelicula=True) -> list[dict]:
    filtros, parametros = _filtros_funcion(local, periodo)
    condiciones = " AND ".join(["e.estado IN ('comprada', 'utilizada')"] + filtros)
    pelicula_select = "f.id_pelicula," if por_pelicula else ""
    pelicula_grupo = "activas.id_pelicula," if por_pelicula else ""
    query = """
        SELECT {pelicula_grupo} ds.id_servicio, serv.nombre, serv.categoria,
               SUM(ds.cantidad) AS cantidad,
               SUM(ds.cantidad * ds.precio_historico) AS ingresos
        FROM (
            SELECT DISTINCT {pelicula_select} e.id_compra
            FROM entradas e
            INNER JOIN funciones f ON f.id = e.id_funcion
            INNER JOIN salas s ON s.id = f.id_sala
            WHERE {condiciones}
        ) activas
        INNER JOIN detalles_servicios ds ON ds.id_compra = activas.id_compra AND ds.cantidad > 0
        INNER JOIN servicios serv ON serv.id = ds.id_servicio
        GROUP BY {pelicula_grupo} ds.id_servicio, serv.nombre, serv.categoria
        ORDER BY {pelicula_grupo} cantidad DESC, serv.nombre ASC, ds.id_servicio ASC
    """.format(condiciones=condiciones, pelicula_select=pelicula_select, pelicula_grupo=pelicula_grupo)
    return ejecutar_consulta(query, tuple(parametros) or None)


def obtener_periodos_ocupacion(local=None) -> list[dict]:
    query = """
        SELECT DISTINCT YEAR(f.fecha_hora_proyeccion) AS anio, MONTH(f.fecha_hora_proyeccion) AS mes
        FROM funciones f INNER JOIN salas s ON s.id = f.id_sala
        WHERE f.eliminada = FALSE {local_where}
        ORDER BY anio DESC, mes DESC
    """
    return ejecutar_consulta(query.format(local_where="AND s.local = %s" if local else ""), (local,) if local else None)


def obtener_metricas_ocupacion_por_funcion(local=None, periodo=None, incluir_eliminadas=False) -> list[dict]:
    """
    calcula la ocupacion individual de cada funcion especifica,
    incluyendo entradas canceladas e ingresos monetarios.
    """
    query = """
            SELECT
                f.id AS id_funcion,
                f.fecha_hora_proyeccion,
                p.titulo AS pelicula_titulo,
                s.nombre AS sala_nombre,
                s.local AS cine_local,
                s.capacidad AS sala_capacidad,
                COUNT(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.id END) AS butacas_ocupadas,
                COUNT(CASE WHEN e.estado = 'cancelada' THEN e.id END) AS butacas_canceladas,
                s.capacidad - COUNT(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.id END) AS butacas_libres,
                COALESCE(SUM(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.precio_historico ELSE 0 END), 0) AS total_ingresos
            FROM funciones f
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
                     INNER JOIN salas s ON f.id_sala = s.id
                     LEFT JOIN entradas e ON f.id = e.id_funcion
            WHERE {filtro_eliminadas} {filtro_local}
            GROUP BY f.id, f.fecha_hora_proyeccion, p.titulo, s.nombre, s.local, s.capacidad
            ORDER BY f.fecha_hora_proyeccion DESC
            """
    filtros, parametros = _filtros_funcion(local, periodo)
    return ejecutar_consulta(query.format(
        filtro_eliminadas="1 = 1" if incluir_eliminadas else "f.eliminada = FALSE",
        filtro_local=("AND " + " AND ".join(filtros)) if filtros else "",
    ), tuple(parametros) or None)


def obtener_resumen_general_ocupacion(local=None, periodo=None) -> dict:
    """
    calcula los totales (vendidas, canceladas, generadas e ingresos totales).
    """
    query = """
            SELECT
                COUNT(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN 1 END) AS total_vendidas,
                COUNT(CASE WHEN e.estado = 'cancelada' THEN 1 END) AS total_canceladas,
                COUNT(*) AS total_generadas,
                COALESCE(SUM(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.precio_historico ELSE 0 END), 0) AS total_ingresos
            FROM entradas e
            INNER JOIN funciones f ON e.id_funcion = f.id
            INNER JOIN salas s ON f.id_sala = s.id
            {where}
            """
    filtros, parametros = _filtros_funcion(local, periodo)
    resultados = ejecutar_consulta(query.format(where=("WHERE " + " AND ".join(filtros)) if filtros else ""), tuple(parametros) or None)
    return resultados[0] if resultados else {
        "total_vendidas": 0,
        "total_canceladas": 0,
        "total_generadas": 0,
        "total_ingresos": 0,
    }


def obtener_ventas_por_genero(local=None, periodo=None) -> list[dict]:
    """
    calcula entradas vendidas e ingresos agrupados por genero
    """
    query = """
            SELECT
                p.genero,
                COUNT(e.id) AS total_entradas,
                COALESCE(SUM(e.precio_historico), 0) AS total_ingresos
            FROM entradas e
                     INNER JOIN funciones f ON e.id_funcion = f.id
                     INNER JOIN salas s ON f.id_sala = s.id
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
            WHERE e.estado IN ('comprada', 'utilizada')
              {local_where}
            GROUP BY p.genero
            ORDER BY total_entradas DESC
            """
    filtros, parametros = _filtros_funcion(local, periodo)
    return ejecutar_consulta(query.format(local_where=("AND " + " AND ".join(filtros)) if filtros else ""), tuple(parametros) or None)


def obtener_ventas_por_franja_horaria(local=None, periodo=None) -> list[dict]:
    """
    calcula entradas vendidas e ingresos agrupados por hora de proyeccion
    """
    query = """
            SELECT
                HOUR(f.fecha_hora_proyeccion) AS hora,
                COUNT(e.id) AS total_entradas,
                COALESCE(SUM(e.precio_historico), 0) AS total_ingresos
            FROM entradas e
                INNER JOIN funciones f ON e.id_funcion = f.id
            INNER JOIN salas s ON f.id_sala = s.id
            WHERE e.estado IN ('comprada', 'utilizada')
              {local_where}
            GROUP BY HOUR(f.fecha_hora_proyeccion)
            ORDER BY hora ASC
            """
    filtros, parametros = _filtros_funcion(local, periodo)
    return ejecutar_consulta(query.format(local_where=("AND " + " AND ".join(filtros)) if filtros else ""), tuple(parametros) or None)