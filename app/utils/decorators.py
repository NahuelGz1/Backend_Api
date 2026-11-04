import os
from functools import wraps
from flask import request
from app.utils.response import responder_error
from app.utils.constantes import ROL_ADMINISTRADOR

try:
    import jwt
except ImportError:
    jwt = None

CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "clave_secreta_cine_paradiso")


def requiere_autenticacion(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return responder_error(code=401, message="Token de autenticación faltante")

        try:
            token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else auth_header
            datos_usuario = jwt.decode(token, CLAVE_SECRETA, algorithms=["HS256"])
            request.usuario_actual = datos_usuario
        except jwt.ExpiredSignatureError:
            return responder_error(code=401, message="El token ha expirado")
        except (jwt.InvalidTokenError, Exception):
            return responder_error(code=401, message="Token inválido")

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