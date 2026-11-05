from app.db import ejecutar_consulta, ejecutar_mutacion


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


def crear_usuario(nombre: str, email: str, password_hash: str, rol: str = "cliente") -> dict:
    """Inserta un nuevo usuario en la base de datos utilizando el helper centralizado."""
    sql = """
          INSERT INTO usuarios (nombre, email, password_hash, rol)
          VALUES (%s, %s, %s, %s) \
          """
    nuevo_id = ejecutar_mutacion(sql, (nombre, email, password_hash, rol))

    return {
        "id": nuevo_id,
        "nombre": nombre,
        "email": email,
        "rol": rol
    }


def obtener_historial_servicios_por_usuario(id_usuario: int) -> list:
    """Obtiene las compras de servicios del usuario alineando alias con la capa de servicios."""
    query = """
            SELECT
                cs.id AS id_compra_servicio,
                cs.fecha_hora_compra,
                s.id AS id_servicio,
                s.nombre AS servicio_nombre,
                s.precio
            FROM compras_servicios cs
                     INNER JOIN servicios s ON cs.id_servicio = s.id
            WHERE cs.id_usuario = %s
            ORDER BY cs.fecha_hora_compra DESC \
            """
    return ejecutar_consulta(query, (id_usuario,))


def obtener_historial_entradas_por_usuario(id_usuario: int) -> list:
    """Obtiene el historial de entradas con todos los alias requeridos por auth_service."""
    query = """
            SELECT
                e.id AS id_entrada,
                e.numero_butaca,
                e.codigo_qr,
                e.estado,
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
    return ejecutar_consulta(query, (id_usuario,))