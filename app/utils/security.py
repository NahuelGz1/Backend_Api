import os
from datetime import datetime, timedelta, timezone
from werkzeug.security import check_password_hash, generate_password_hash

CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "clave_secreta_cine_paradiso")


def hashear_contraseña(contraseña: str) -> str:
    return generate_password_hash(contraseña)


def verificar_contraseña(contraseña: str, contraseña_hash: str) -> bool:
    return check_password_hash(contraseña_hash, contraseña)


hashear_password = hashear_contraseña
verificar_password = verificar_contraseña


def generar_token_acceso(usuario_id: int, rol: str) -> str:
    try:
        import jwt
    except ImportError:
        raise ImportError("La librería 'PyJWT' es requerida para generar tokens.")

    payload = {
        "sub": usuario_id,
        "id": usuario_id,
        "rol": rol.lower(),
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, CLAVE_SECRETA, algorithm="HS256")