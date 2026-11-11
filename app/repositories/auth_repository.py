from app.db import ejecutar_consulta, ejecutar_mutacion
from pymysql.err import IntegrityError


def obtener_credenciales_por_id(id_usuario):
    filas = ejecutar_consulta(
        "SELECT id, nombre, email, password_hash, rol FROM usuarios WHERE id = %s",
        (id_usuario,),
    )
    return filas[0] if filas else None


def restablecer_password(id_usuario, hash_anterior, nuevo_hash):
    return ejecutar_mutacion(
        "UPDATE usuarios SET password_hash = %s WHERE id = %s AND password_hash = %s",
        (nuevo_hash, id_usuario, hash_anterior),
    )


def obtener_usuario_por_id(id_usuario: int) -> dict | None:
    """Busca un usuario por su ID."""
    query = """
            SELECT id, nombre, email, rol
            FROM usuarios
            WHERE id = %s \
            """
    resultados = ejecutar_consulta(query, (id_usuario,))
    return resultados[0] if resultados else None


def buscar_por_email(email: str) -> dict | None:
    """Busca un usuario por su correo electrónico."""
    query = """
            SELECT id, nombre, email, password_hash, rol
            FROM usuarios
            WHERE email = %s \
            """
    resultados = ejecutar_consulta(query, (email,))
    return resultados[0] if resultados else None


def obtener_password_hash_por_id(id_usuario: int) -> str | None:
    """Obtiene la contraseña cifrada de un usuario mediante su ID. Devuelve None si el usuario no existe."""
    sql = """
        SELECT password_hash
        FROM usuarios
        WHERE id = %s
    """

    resultados = ejecutar_consulta(sql, (id_usuario,))

    return resultados[0]["password_hash"] if resultados else None


def actualizar_password_hash(id_usuario: int, nuevo_hash: str) -> int:
    """Actualiza la contraseña cifrada de un usuario. Devuelve el resultado de la operación en la base de datos."""
    sql = """
        UPDATE usuarios
        SET password_hash = %s
        WHERE id = %s
    """

    return ejecutar_mutacion(sql, (nuevo_hash, id_usuario))


def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> dict:
    """Inserta un nuevo usuario en la base de datos utilizando el helper centralizado."""
    sql = """
          INSERT INTO usuarios (nombre, email, password_hash, rol)
          VALUES (%s, %s, %s, %s) \
          """
    try:
        nuevo_id = ejecutar_mutacion(sql, (nombre, email, password_hash, rol))
    except IntegrityError as error:
        if error.args[0] == 1062:
            raise ValueError("El correo electrónico ya se encuentra registrado.", 409) from error
        raise

    return {
        "id": nuevo_id,
        "nombre": nombre,
        "email": email,
        "rol": rol
    }


def actualizar_rol_usuario(id_usuario: int, rol: str) -> int:
    """Actualiza el rol de una cuenta y devuelve la cantidad de filas afectadas."""
    return ejecutar_mutacion(
        "UPDATE usuarios SET rol = %s WHERE id = %s",
        (rol, id_usuario),
    )


def listar_administradores() -> list[dict]:
    return ejecutar_consulta(
        "SELECT id, nombre, email, rol FROM usuarios "
        "WHERE rol = %s ORDER BY email",
        ("administrador",),
    )


def obtener_historial_servicios_por_usuario(id_usuario: int) -> list:
    """Obtiene las compras de servicios del usuario alineando alias con la capa de servicios."""
    query_nuevo = """
            SELECT
                ds.id AS id_compra_servicio,
                ds.cantidad,
                c.fecha_hora AS fecha_hora_compra,
                s.id AS id_servicio,
                s.nombre AS servicio_nombre,
                ds.precio_historico AS precio
            FROM detalles_servicios ds
                     INNER JOIN compras c ON ds.id_compra = c.id
                     INNER JOIN servicios s ON ds.id_servicio = s.id
            WHERE c.id_usuario = %s
            ORDER BY c.fecha_hora DESC \
            """
    try:
        return ejecutar_consulta(query_nuevo, (id_usuario,))
    except Exception:
        # Fallback para bases de datos con el esquema anterior (tabla compras_servicios)
        query_viejo = """
            SELECT
                cs.id AS id_compra_servicio,
                1 AS cantidad,
                cs.fecha_hora_compra,
                s.id AS id_servicio,
                s.nombre AS servicio_nombre,
                s.precio
            FROM compras_servicios cs
                     INNER JOIN servicios s ON cs.id_servicio = s.id
            WHERE cs.id_usuario = %s
            ORDER BY cs.fecha_hora_compra DESC \
            """
        return ejecutar_consulta(query_viejo, (id_usuario,))


def obtener_historial_entradas_por_usuario(id_usuario: int) -> list:
    """Obtiene el historial de entradas con todos los alias requeridos por auth_service."""
    query_nuevo = """
            SELECT
                e.id AS id_entrada,
                e.numero_butaca,
                e.codigo_qr,
                e.estado,
                e.precio_historico,
                c.id AS id_compra,
                f.id AS id_funcion,
                f.fecha_hora_proyeccion,
                p.titulo AS pelicula_titulo,
                p.poster AS pelicula_poster,
                p.duracion AS pelicula_duracion,
                s.nombre AS sala_nombre,
                s.local AS cine_local
            FROM entradas e
                     INNER JOIN compras c ON e.id_compra = c.id
                     INNER JOIN funciones f ON e.id_funcion = f.id
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
                     INNER JOIN salas s ON f.id_sala = s.id
            WHERE c.id_usuario = %s
            ORDER BY f.fecha_hora_proyeccion DESC \
            """
    try:
        return ejecutar_consulta(query_nuevo, (id_usuario,))
    except Exception:
        # Fallback para bases de datos con el esquema anterior (entradas con id_usuario)
        query_viejo = """
            SELECT
                e.id AS id_entrada,
                e.numero_butaca,
                e.codigo_qr,
                e.estado,
                NULL AS precio_historico,
                e.id AS id_compra,
                f.id AS id_funcion,
                f.fecha_hora_proyeccion,
                p.titulo AS pelicula_titulo,
                p.poster AS pelicula_poster,
                p.duracion AS pelicula_duracion,
                s.nombre AS sala_nombre,
                s.local AS cine_local
            FROM entradas e
                     INNER JOIN funciones f ON e.id_funcion = f.id
                     INNER JOIN peliculas p ON f.id_pelicula = p.id
                     INNER JOIN salas s ON f.id_sala = s.id
            WHERE e.id_usuario = %s
            ORDER BY f.fecha_hora_proyeccion DESC \
            """
        return ejecutar_consulta(query_viejo, (id_usuario,))


def actualizar_usuario(id_usuario: int, datos: dict) -> int:
    """Actualiza únicamente las columnas existentes (nombre, email) de un usuario."""
    campos_permitidos = ["nombre", "email"]
    asignaciones = []
    valores = []

    for campo in campos_permitidos:
        if campo in datos and datos[campo]:
            asignaciones.append(f"{campo} = %s")
            valores.append(datos[campo])

    if not asignaciones:
        return 0

    sql = f"UPDATE usuarios SET {', '.join(asignaciones)} WHERE id = %s"
    valores.append(id_usuario)

    try:
        return ejecutar_mutacion(sql, tuple(valores))
    except IntegrityError as error:
        if error.args[0] == 1062:
            raise ValueError("El correo electrónico ya se encuentra registrado.") from error
        raise