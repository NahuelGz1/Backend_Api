import re


def validar_email(email):
    if not isinstance(email, str):
        raise ValueError("Ingresá un correo electrónico válido", 400)
    email = email.strip().lower()
    if len(email) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Ingresá un correo electrónico válido", 400)
    return email


def validar_password(password):
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        raise ValueError("La contraseña debe tener entre 8 y 128 caracteres", 400)
    return password


def validar_nombre(nombre):
    if not isinstance(nombre, str) or not 1 <= len(nombre.strip()) <= 100:
        raise ValueError("El nombre debe tener entre 1 y 100 caracteres", 400)
    return nombre.strip()