from app.db import ejecutar_consulta

def obtener_metricas_ocupacion_por_pelicula() -> list[dict]:
    """
    Calcula para cada película:
    - Entradas vendidas (compradas o utilizadas)
    - Entradas canceladas
    - Capacidad total de butacas ofertadas en sus funciones
    - Porcentaje de ocupación
    """
    query = """
            SELECT
                peliculas.id AS id_pelicula,
                peliculas.titulo AS pelicula_titulo,
                peliculas.genero,
                COUNT(DISTINCT funciones.id) AS total_funciones,
                COALESCE(SUM(salas.capacidad), 0) AS capacidad_total_ofertada,
                COALESCE(SUM(CASE WHEN entradas.estado IN ('comprada', 'utilizada') THEN 1 ELSE 0 END), 0) AS total_entradas_vendidas,
                COALESCE(SUM(CASE WHEN entradas.estado = 'cancelada' THEN 1 ELSE 0 END), 0) AS total_entradas_canceladas
            FROM peliculas
                     LEFT JOIN funciones ON peliculas.id = funciones.id_pelicula
                     LEFT JOIN salas ON funciones.id_sala = salas.id
                     LEFT JOIN entradas ON funciones.id = entradas.id_funcion
            GROUP BY peliculas.id, peliculas.titulo, peliculas.genero
            ORDER BY total_entradas_vendidas DESC \
            """
    return ejecutar_consulta(query)


def obtener_metricas_ocupacion_por_funcion() -> list[dict]:
    """
    Calcula la ocupación individual de cada función específica.
    """
    query = """
            SELECT
                funciones.id AS id_funcion,
                funciones.fecha_hora_proyeccion,
                peliculas.titulo AS pelicula_titulo,
                salas.nombre AS sala_nombre,
                salas.local AS cine_local,
                salas.capacidad AS sala_capacidad,
                COUNT(CASE WHEN entradas.estado IN ('comprada', 'utilizada') THEN entradas.id END) AS butacas_ocupadas,
                salas.capacidad - COUNT(CASE WHEN entradas.estado IN ('comprada', 'utilizada') THEN entradas.id END) AS butacas_libres
            FROM funciones
                     INNER JOIN peliculas ON funciones.id_pelicula = peliculas.id
                     INNER JOIN salas ON funciones.id_sala = salas.id
                     LEFT JOIN entradas ON funciones.id = entradas.id_funcion
            GROUP BY funciones.id, funciones.fecha_hora_proyeccion, peliculas.titulo, salas.nombre, salas.local, salas.capacidad
            ORDER BY funciones.fecha_hora_proyeccion DESC \
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
        "total_generadas": 0
    }