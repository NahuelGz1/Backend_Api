from app.db import ejecutar_consulta


def obtener_metricas_ocupacion_por_pelicula() -> list[dict]:
    """
    Calcula por película:
    - Entradas vendidas (compradas o utilizadas)
    - Entradas canceladas
    - Capacidad total ofertada
    - Total recaudado en dinero (total_ingresos)
    """
    query = """
            SELECT
                p.id AS id_pelicula,
                p.titulo AS pelicula_titulo,
                p.genero,
                COUNT(DISTINCT f.id) AS total_funciones,
                COALESCE((
                             SELECT SUM(s_sub.capacidad)
                             FROM funciones f_sub
                                      INNER JOIN salas s_sub ON f_sub.id_sala = s_sub.id
                             WHERE f_sub.id_pelicula = p.id
                         ), 0) AS capacidad_total_ofertada,
                COALESCE(SUM(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN 1 ELSE 0 END), 0) AS total_entradas_vendidas,
                COALESCE(SUM(CASE WHEN e.estado = 'cancelada' THEN 1 ELSE 0 END), 0) AS total_entradas_canceladas,
                COALESCE(SUM(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.precio_historico ELSE 0 END), 0) AS total_ingresos
            FROM peliculas p
                     LEFT JOIN funciones f ON p.id = f.id_pelicula
                     LEFT JOIN entradas e ON f.id = e.id_funcion
            GROUP BY p.id, p.titulo, p.genero
            ORDER BY total_entradas_vendidas DESC
            """
    return ejecutar_consulta(query)


def obtener_metricas_ocupacion_por_funcion() -> list[dict]:
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
                COALESCE(SUM(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.precio_historico_historico ELSE 0 END), 0) AS total_ingresos
            FROM funciones f
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
                     INNER JOIN salas s ON f.id_sala = s.id
                     LEFT JOIN entradas e ON f.id = e.id_funcion
            GROUP BY f.id, f.fecha_hora_proyeccion, p.titulo, s.nombre, s.local, s.capacidad
            ORDER BY f.fecha_hora_proyeccion DESC
            """
    return ejecutar_consulta(query)


def obtener_resumen_general_ocupacion() -> dict:
    """
    calcula los totales (vendidas, canceladas, generadas e ingresos totales).
    """
    query = """
            SELECT
                COUNT(CASE WHEN estado IN ('comprada', 'utilizada') THEN 1 END) AS total_vendidas,
                COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) AS total_canceladas,
                COUNT(*) AS total_generadas,
                COALESCE(SUM(CASE WHEN estado IN ('comprada', 'utilizada') THEN precio ELSE 0 END), 0) AS total_ingresos
            FROM entradas
            """
    resultados = ejecutar_consulta(query)
    return resultados[0] if resultados else {
        "total_vendidas": 0,
        "total_canceladas": 0,
        "total_generadas": 0,
        "total_ingresos": 0,
    }


def obtener_ventas_por_genero() -> list[dict]:
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
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
            WHERE e.estado IN ('comprada', 'utilizada')
            GROUP BY p.genero
            ORDER BY total_entradas DESC
            """
    return ejecutar_consulta(query)


def obtener_ventas_por_franja_horaria() -> list[dict]:
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
            WHERE e.estado IN ('comprada', 'utilizada')
            GROUP BY HOUR(f.fecha_hora_proyeccion)
            ORDER BY hora ASC
            """
    return ejecutar_consulta(query)