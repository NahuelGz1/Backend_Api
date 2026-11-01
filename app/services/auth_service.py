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

