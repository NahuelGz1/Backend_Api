import re
from .response import construir_error_api

def validar_string_no_vacio(valor, nombre: str) -> str:
    if valor is None or not str(valor).strip():
        raise ValueError(
            construir_error_api(
                code=f'required.{nombre}',
                message=f"Campo requerido: '{nombre}'",
                description=f"El campo '{nombre}' es obligatorio y no puede estar vacío"
            ),
            400
        )
    return str(valor).strip()

def validar_email(email: str) -> str:
    email_limpio = validar_string_no_vacio(email, 'email').lower()
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(patron, email_limpio):
        raise ValueError(
            construir_error_api(
                code='invalid.email',
                message='Formato de email inválido',
                description="El campo 'email' debe ser una dirección de correo válida"
            ),
            400
        )
    return email_limpio

def validar_paginacion(args: dict):
    if "limit" in args or "offset" in args:
        raise ValueError(
            construir_error_api(
                code="invalid_param",
                message="Parámetro inválido",
                description="'limit' y 'offset' están mal escritos, deben ser '_limit' y '_offset'"
            ),
            400
        )
    try:
        limit = int(args.get("_limit", 10))
        offset = int(args.get("_offset", 0))
    except ValueError:
        raise ValueError(
            construir_error_api(
                code="invalid_param",
                message="Parámetro inválido",
                description="limit y offset deben ser números enteros"
            ),
            400
        )
    if not (1 <= limit <= 100) or offset < 0:
        raise ValueError(
            construir_error_api(
                code="invalid_param",
                message="Parámetro inválido",
                description="limit debe estar entre 1 y 100, y offset no puede ser negativo"
            ),
            400
        )
    return limit, offset