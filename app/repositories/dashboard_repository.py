from app.db import ejecutar_consulta


def obtener_metricas_ocupacion_por_pelicula() -> list[dict]:
    """
    Calcula por película:
    - Entradas vendidas (compradas o utilizadas)
    - Entradas canceladas
    - Capacidad total ofertada (calculada correctamente sin multiplicar por N entradas)
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
                COALESCE(SUM(CASE WHEN e.estado = 'cancelada' THEN 1 ELSE 0 END), 0) AS total_entradas_canceladas
            FROM peliculas p
                     LEFT JOIN funciones f ON p.id = f.id_pelicula
                     LEFT JOIN entradas e ON f.id = e.id_funcion
            GROUP BY p.id, p.titulo, p.genero
            ORDER BY total_entradas_vendidas DESC \
            """
    return ejecutar_consulta(query)


def obtener_metricas_ocupacion_por_funcion() -> list[dict]:
    """
    Calcula la ocupación individual de cada función específica.
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
                s.capacidad - COUNT(CASE WHEN e.estado IN ('comprada', 'utilizada') THEN e.id END) AS butacas_libres
            FROM funciones f
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
                     INNER JOIN salas s ON f.id_sala = s.id
                     LEFT JOIN entradas e ON f.id = e.id_funcion
            GROUP BY f.id, f.fecha_hora_proyeccion, p.titulo, s.nombre, s.local, s.capacidad
            ORDER BY f.fecha_hora_proyeccion DESC \
            """
    return ejecutar_consulta(query)


def obtener_resumen_general_ocupacion() -> dict:
    """
    Calcula los totales globales para tarjetas o gráficos del dashboard.
    """
    query = """
            SELECT
                COUNT(CASE WHEN estado IN ('comprada', 'utilizada') THEN 1 END) AS total_vendidas,
                COUNT(CASE WHEN estado = 'cancelada' THEN 1 END) AS total_canceladas,
                COUNT(*) AS total_generadas
            FROM entradas \
            """
    resultados = ejecutar_consulta(query)
    return resultados[0] if resultados else {
        "total_vendidas": 0,
        "total_canceladas": 0,
        "total_generadas": 0,
    }