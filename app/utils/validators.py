import re


def validar_string_no_vacio(valor, nombre: str) -> str:
    """Valida que un campo de texto no esté vacío."""
    if valor is None or not str(valor).strip():
        raise ValueError(f"El campo '{nombre}' es obligatorio y no puede estar vacío", 400)
    return str(valor).strip()


def validar_email(email: str) -> str:
    """Valida el formato de un correo electrónico."""
    email_limpio = validar_string_no_vacio(email, "email").lower()
    patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(patron, email_limpio):
        raise ValueError("El campo 'email' debe ser una dirección de correo válida", 400)
    return email_limpio


def validar_paginacion(args: dict) -> tuple[int, int]:
    """Valida los parámetros de paginación opcionales _limit y _offset."""
    if "limit" in args or "offset" in args:
        raise ValueError("Los parámetros 'limit' y 'offset' deben renombrarse a '_limit' y '_offset'", 400)

    try:
        limit = int(args.get("_limit", 10))
        offset = int(args.get("_offset", 0))
    except (ValueError, TypeError):
        raise ValueError("Los parámetros '_limit' y '_offset' deben ser números enteros", 400)

    if not (1 <= limit <= 100) or offset < 0:
        raise ValueError("El límite debe estar entre 1 y 100, y el offset no puede ser negativo", 400)

    return limit, offset