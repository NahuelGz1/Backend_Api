import os
from datetime import datetime, timedelta, timezone
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

CLAVE_SECRETA = os.getenv("JWT_SECRET_KEY", "clave_secreta_cine_paradiso")

def hashear_contraseña(contraseña: str) -> str:
    return generate_password_hash(contraseña)

def verificar_contraseña(contraseña: str, contraseña_hash: str) -> bool:
    return check_password_hash(contraseña_hash, contraseña)

def generar_token_acceso(usuario_id: int, rol: str) -> str:
    payload = {
        "sub": usuario_id,
        "rol": rol,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    return jwt.encode(payload, CLAVE_SECRETA, algorithm="HS256")