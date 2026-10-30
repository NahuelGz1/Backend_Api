"""Consultas SQL de películas y de las funciones vigentes."""

from datetime import datetime, timedelta, timezone
from db import obtener_conexion


def _ahora():
    """Devuelve la hora actual de Argentina (UTC-3) como datetime sin zona horaria.

    Las funciones se guardan con hora argentina. Si el servidor corre en otra
    zona (por ejemplo UTC), datetime.now() daría una hora corrida y la cartelera
    escondería funciones que todavía no empezaron.
    """
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _ejecutar_consulta(sql, parametros=()):
    """Ejecuta un SELECT y devuelve una lista de diccionarios (uno por fila)."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)

        # Si la consulta no devuelve columnas (por ejemplo un INSERT) no hay filas que armar
        if cursor.description is None:
            cursor.close()
            return []

        filas_crudas = cursor.fetchall()

        # Nombres de las columnas, para usarlos como claves del diccionario
        nombres_columnas = []
        for columna in cursor.description:
            nombres_columnas.append(columna[0])

        # Armamos la lista de diccionarios
        lista_de_diccionarios = []
        for fila in filas_crudas:
            diccionario_fila = {}
            for i in range(len(nombres_columnas)):
                nombre = nombres_columnas[i]
                valor = fila[i]
                diccionario_fila[nombre] = valor
            lista_de_diccionarios.append(diccionario_fila)

        cursor.close()
        return lista_de_diccionarios
    finally:
        conexion.close()


def _ejecutar_insert(sql, parametros):
    """Ejecuta un INSERT y devuelve el id de la fila nueva."""
    conexion = obtener_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, parametros)
        conexion.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        return nuevo_id
    finally:
        conexion.close()


def _sql_funciones_vigentes(solo_una_pelicula=False):
    """Arma el SQL de las funciones vigentes (el primer %s es la fecha y hora actual).

    Si solo_una_pelicula es True, agrega el filtro por película (otro %s, el id).
    """
    sql = """
        SELECT funciones.id, funciones.id_pelicula, funciones.fecha_hora_proyeccion,
               salas.nombre AS sala, salas.local, salas.capacidad
        FROM funciones
        JOIN salas ON salas.id = funciones.id_sala
        WHERE funciones.fecha_hora_proyeccion > %s
    """
    if solo_una_pelicula:
        sql = sql + " AND funciones.id_pelicula = %s"

    return sql + " ORDER BY funciones.fecha_hora_proyeccion"


def listar_peliculas_en_cartelera():
    """Películas que tienen al menos una función vigente."""
    sql = """
        SELECT peliculas.id, peliculas.titulo, peliculas.sinopsis, peliculas.poster, peliculas.duracion,
               peliculas.clasificacion, peliculas.genero
        FROM peliculas
        WHERE EXISTS (
            SELECT 1
            FROM funciones
            WHERE funciones.id_pelicula = peliculas.id
              AND funciones.fecha_hora_proyeccion > %s
        )
        ORDER BY peliculas.titulo
    """
    return _ejecutar_consulta(sql, (_ahora(),))


def listar_funciones_vigentes():
    """Todas las funciones vigentes, de todas las películas."""
    sql_completo = _sql_funciones_vigentes()
    return _ejecutar_consulta(sql_completo, (_ahora(),))


def listar_funciones_vigentes_de_pelicula(pelicula_id):
    sql_completo = _sql_funciones_vigentes(solo_una_pelicula=True)
    # Los parámetros van en el mismo orden que los %s: primero la fecha, después el id
    return _ejecutar_consulta(sql_completo, (_ahora(), pelicula_id))


def buscar_por_id(pelicula_id):
    """Devuelve la película como diccionario, o None si no existe."""
    sql = """
        SELECT id, titulo, sinopsis, poster, duracion, clasificacion, genero
        FROM peliculas
        WHERE id = %s
    """
    filas = _ejecutar_consulta(sql, (pelicula_id,))

    if len(filas) > 0:
        return filas[0]
    else:
        return None


def existe_pelicula(titulo, duracion):
    """Dice si ya hay una película con ese título y esa duración.

    MySQL compara los textos sin distinguir mayúsculas ni tildes, así que
    "El Rey León" y "el rey leon" cuentan como el mismo título.
    """
    sql = """
        SELECT id
        FROM peliculas
        WHERE titulo = %s AND duracion = %s
    """
    filas = _ejecutar_consulta(sql, (titulo, duracion))
    return len(filas) > 0


def insertar(pelicula):
    """Guarda una película nueva y devuelve su id."""
    sql = """
        INSERT INTO peliculas (titulo, sinopsis, poster, duracion, clasificacion, genero)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    parametros = (
        pelicula["titulo"],
        pelicula["sinopsis"],
        pelicula["poster"],
        pelicula["duracion"],
        pelicula["clasificacion"],
        pelicula["genero"],
    )
    return _ejecutar_insert(sql, parametros)
