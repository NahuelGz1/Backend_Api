import hmac
from functools import wraps
from flask import request
import jwt
from app.repositories.auth_repository import obtener_credenciales_por_id
from app.utils.security import clave_secreta, version_credencial
from app.utils.response import responder_error
from app.utils.constantes import ROL_ADMINISTRADOR

def requiere_autenticacion(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return responder_error(code=401, message="Token de autenticación faltante")

        try:
            token = auth_header[7:]
            datos_usuario = jwt.decode(
                token, clave_secreta(), algorithms=["HS256"],
                options={"require": ["sub", "exp", "ver"]},
            )
        except jwt.ExpiredSignatureError:
            return responder_error(code=401, message="El token ha expirado")
        except jwt.InvalidTokenError:
            return responder_error(code=401, message="Token inválido")

        usuario = obtener_credenciales_por_id(datos_usuario["sub"])
        version = datos_usuario.get("ver")
        if not usuario or not isinstance(version, str) or not hmac.compare_digest(
            version, version_credencial(usuario["password_hash"])
        ):
            return responder_error(code=401, message="La sesión ya no es válida")
        datos_usuario["rol"] = usuario["rol"]
        request.usuario_actual = datos_usuario
        return f(*args, **kwargs)

    return decorated


def requiere_administrador(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = getattr(request, "usuario_actual", None)
        rol = str(usuario.get("rol", "")).lower() if usuario else ""
        if not usuario or rol != ROL_ADMINISTRADOR:
            return responder_error(code=403, message="Acceso restringido a administradores")
        return f(*args, **kwargs)

    return decorated