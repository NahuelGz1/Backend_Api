import os
from functools import wraps
from flask import request, g
try:
    import jwt
except ImportError:
    jwt = None
from app.utils.response import responder_error

CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "clave_secreta_cine_paradiso")

def requiere_autenticacion(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return responder_error(401, "Token de autenticación faltante")

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            datos_usuario = jwt.decode(token, CLAVE_SECRETA, algorithms=["HS256"])
            request.usuario_actual = datos_usuario
        except jwt.ExpiredSignatureError:
            return responder_error(401, "El token ha expirado")
        except jwt.InvalidTokenError:
            return responder_error(401, "Token inválido")

        return f(*args, **kwargs)
    return decorated

def requiere_administrador(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = getattr(request, 'usuario_actual', None)
        if not usuario or usuario.get('rol') != 'ADMIN':
            return responder_error(403, "Acceso restringido a administradores")
        return f(*args, **kwargs)
    return decorated