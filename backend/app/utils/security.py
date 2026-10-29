from werkzeug.security import generate_password_hash, check_password_hash

def hashear_password(password:str) -> str:
    return generate_password_hash(password)

def verificar_password(password_plano:str,password_hash:str) -> bool:
    return check_password_hash(password_hash, password_plano)