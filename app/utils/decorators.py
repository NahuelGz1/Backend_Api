import os
from functools import wraps
from flask import request, g
import jwt
from app.utils.response import responder_error

CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "clave_secreta_cine_paradiso")

def requiere_autenticacion(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return responder_error("Token de autenticación faltante", 401)

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            datos_usuario = jwt.decode(token, CLAVE_SECRETA, algorithms=["HS256"])
            request.usuario_actual = datos_usuario
        except jwt.ExpiredSignatureError:
            return responder_error("El token ha expirado", 401)
        except jwt.InvalidTokenError:
            return responder_error("Token inválido", 401)

        return f(*args, **kwargs)
    return decorated

def requiere_administrador(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = getattr(request, 'usuario_actual', None)
        if not usuario or usuario.get('rol') != 'ADMIN':
            return responder_error("Acceso restringido a administradores", 403)
        return f(*args, **kwargs)
    return decorated