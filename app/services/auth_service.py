from app.repositories.auth_repository import buscar_por_email, crear_usuario
from app.utils.security import verificar_contraseña, generar_token_acceso, hashear_contraseña


def registrar_usuario(nombre: str, email: str, password: str, rol: str = "cliente") -> dict:
    """
    Registra un nuevo usuario cifrando su contraseña.
    Lanza ValueError si el email ya existe o si ocurre un error de base de datos.
    """
    try:
        if buscar_por_email(email):
            raise ValueError("El correo electrónico ya se encuentra registrado.")

        password_hash = hashear_contraseña(password)
        resultado = crear_usuario(nombre=nombre, email=email, password_hash=password_hash, rol=rol)

        if "error" in resultado:
            raise ValueError(resultado["error"])

        return resultado
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error al registrar usuario: {str(e)}")


def autenticar_usuario(email: str, password: str) -> dict:
    """
    Valida las credenciales del usuario y genera un token JWT de sesión.
    Lanza ValueError si las credenciales son inválidas o si ocurre un fallo.
    """
    try:
        usuario = buscar_por_email(email)

        if not usuario or not verificar_contraseña(password, usuario.get("password_hash", "")):
            raise ValueError("Credenciales inválidas.")

        rol_usuario = usuario.get("rol", "cliente")
        token = generar_token_acceso(usuario["id"], rol_usuario)

        return {
            "token": token,
            "usuario": {
                "id": usuario["id"],
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "rol": rol_usuario
            }
        }
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error en el proceso de autenticación: {str(e)}")

from app.repositories.auth_repository import (
    obtener_usuario_por_id,
    obtener_historial_entradas_por_usuario,
    obtener_historial_servicios_por_usuario
)
from app.utils.dates import datetime_a_string

def consultar_perfil_usuario(id_usuario: int):
    """
    Retorna la información del usuario autenticado.
    """
    usuario = obtener_usuario_por_id(id_usuario)
    if not usuario:
        raise ValueError("Usuario no encontrado", 404)
    return usuario


def consultar_historial_completo_usuario(id_usuario: int) -> dict:
    entradas_bd = obtener_historial_entradas_por_usuario(id_usuario)
    servicios_bd = obtener_historial_servicios_por_usuario(id_usuario)

    lista_entradas = []
    for fila in entradas_bd:
        lista_entradas.append({
            "id_entrada": fila["id_entrada"],
            "numero_butaca": fila["numero_butaca"],
            "codigo_qr": fila["codigo_qr"],
            "estado": fila["estado"],
            "funcion": {
                "id": fila["id_funcion"],
                "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
                "sala": fila["sala_nombre"],
                "local": fila["cine_local"]
            },
            "pelicula": {
                "titulo": fila["pelicula_titulo"],
                "poster": fila["pelicula_poster"],
                "duracion": fila["pelicula_duracion"]
            }
        })

    lista_servicios = []
    for fila in servicios_bd:
        lista_servicios.append({
            "id_compra_servicio": fila["id_compra_servicio"],
            "id_servicio": fila["id_servicio"],
            "servicio": fila["servicio_nombre"],
            "precio": float(fila["precio"]) if fila["precio"] is not None else 0.0,
            "fecha_hora_compra": datetime_a_string(fila["fecha_hora_compra"])
        })

    return {
        "entradas": lista_entradas,
        "servicios": lista_servicios
    }
