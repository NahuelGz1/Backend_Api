import hashlib
from datetime import datetime, timedelta, timezone
from flask import current_app
import jwt
from werkzeug.security import check_password_hash, generate_password_hash

def clave_secreta():
    clave = current_app.config.get("JWT_SECRET_KEY")
    if not clave or len(clave) < 32:
        raise RuntimeError("JWT_SECRET_KEY debe tener al menos 32 caracteres")
    return clave


def version_credencial(password_hash):
    return hashlib.sha256(password_hash.encode()).hexdigest()


def hashear_contraseña(contraseña: str) -> str:
    return generate_password_hash(contraseña)


def verificar_contraseña(contraseña: str, contraseña_hash: str) -> bool:
    return check_password_hash(contraseña_hash, contraseña)


hashear_password = hashear_contraseña
verificar_password = verificar_contraseña


def generar_token_acceso(usuario_id: int, rol: str, password_hash: str) -> str:
    payload = {
        "sub": str(usuario_id),
        "id": usuario_id,
        "rol": rol.lower(),
        "ver": version_credencial(password_hash),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, clave_secreta(), algorithm="HS256")