from app.repositories.auth_repository import (
    buscar_por_email,
    crear_usuario,
    obtener_historial_entradas_por_usuario,
    obtener_historial_servicios_por_usuario,
    obtener_usuario_por_id,
    actualizar_password_hash,
    obtener_password_hash_por_id,
)
from app.utils.dates import datetime_a_string
from app.utils.security import (
    generar_token_acceso,
    hashear_contraseña,
    verificar_contraseña,
)


def registrar_usuario(nombre: str, email: str, password: str, rol: str = "cliente") -> dict:
    """
    Registra un nuevo usuario cifrando su contraseña.
    Lanza ValueError si el email ya existe.
    """
    if buscar_por_email(email):
        raise ValueError("El correo electrónico ya se encuentra registrado.")

    password_hash = hashear_contraseña(password)
    resultado = crear_usuario(nombre=nombre, email=email, password_hash=password_hash, rol=rol)

    if isinstance(resultado, dict) and "error" in resultado:
        raise ValueError(resultado["error"])

    return resultado


def autenticar_usuario(email: str, password: str) -> dict:
    """
    Valida las credenciales del usuario y genera un token JWT de sesión.
    Lanza ValueError(msg, 401) si las credenciales son inválidas.
    """
    usuario = buscar_por_email(email)

    if not usuario or not verificar_contraseña(password, usuario.get("password_hash", "")):
        raise ValueError("Credenciales inválidas", 401)

    rol_usuario = usuario.get("rol", "cliente")
    token = generar_token_acceso(usuario["id"], rol_usuario)

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": rol_usuario,
        },
    }


def consultar_perfil_usuario(id_usuario: int) -> dict:
    """
    Retorna la información del usuario autenticado.
    """
    usuario = obtener_usuario_por_id(id_usuario)
    if not usuario:
        raise ValueError("Usuario no encontrado", 404)
    return usuario


def consultar_historial_completo_usuario(id_usuario: int) -> dict:
    """
    Retorna el historial unificado de entradas y servicios del usuario.
    """
    entradas_bd = obtener_historial_entradas_por_usuario(id_usuario)
    servicios_bd = obtener_historial_servicios_por_usuario(id_usuario)

    lista_entradas = [
        {
            "id_entrada": fila["id_entrada"],
            "numero_butaca": fila["numero_butaca"],
            "codigo_qr": fila["codigo_qr"],
            "estado": fila["estado"],
            "funcion": {
                "id": fila["id_funcion"],
                "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
                "sala": fila["sala_nombre"],
                "local": fila["cine_local"],
            },
            "pelicula": {
                "titulo": fila["pelicula_titulo"],
                "poster": fila["pelicula_poster"],
                "duracion": fila["pelicula_duracion"],
            },
        }
        for fila in entradas_bd
    ]

    lista_servicios = [
        {
            "id_compra_servicio": fila["id_compra_servicio"],
            "id_servicio": fila["id_servicio"],
            "servicio": fila["servicio_nombre"],
            "precio": float(fila["precio"]) if fila["precio"] is not None else 0.0,
            "fecha_hora_compra": datetime_a_string(fila["fecha_hora_compra"]),
        }
        for fila in servicios_bd
    ]

    return {
        "entradas": lista_entradas,
        "servicios": lista_servicios,
    }


def cambiar_contrasena_usuario(id_usuario: int, contrasena_actual: str, contrasena_nueva: str) -> None:
    """Cambia la contraseña de un usuario autenticado. Verifica la contraseña actual y guarda el hash de la nueva contraseña en la base de datos."""

    if not isinstance(contrasena_actual, str) or not contrasena_actual:
        raise ValueError("Debe ingresar su contraseña actual", 400)

    if not isinstance(contrasena_nueva, str) or not contrasena_nueva:
        raise ValueError("Debe ingresar una contraseña nueva", 400)
    if contrasena_actual == contrasena_nueva:
        raise ValueError(
            "La nueva contraseña debe ser diferente de la actual",
            400
        )

    hash_actual = obtener_password_hash_por_id(id_usuario)

    if hash_actual is None:
        raise ValueError("Usuario no encontrado", 404)

    if not verificar_contraseña(contrasena_actual, hash_actual):
        raise ValueError("La contraseña actual es incorrecta", 400)

    nuevo_hash = hashear_contraseña(contrasena_nueva)

    filas_actualizadas = actualizar_password_hash(id_usuario, nuevo_hash)

    if filas_actualizadas != 1:
        raise ValueError("No se pudo actualizar la contraseña", 500)