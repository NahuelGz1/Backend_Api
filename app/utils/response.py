from flask import jsonify


def responder_exito(data=None, message: str = "Operación exitosa", status_code: int = 200):
    """Retorna una respuesta estandarizada de éxito JSON."""
    body = {
        "ok": True,
        "data": data,
        "message": message
    }
    return jsonify(body), status_code


def responder_error(code: int = 400, message: str = "Error procesando la solicitud", details=None, status_code: int = None):
    """Retorna una respuesta estandarizada de error JSON."""
    if status_code is not None:
        code = status_code
    body = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }
    return jsonify(body), code


def responder_error_de_validacion(error: ValueError, code_por_defecto: int = 400):
    """Responde con el mensaje, el código y el detalle que trae el ValueError (mensaje, código, detalle)."""
    mensaje = error.args[0] if error.args else "Error procesando la solicitud"
    code = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else code_por_defecto
    details = error.args[2] if len(error.args) > 2 else None
    return responder_error(code=code, message=str(mensaje), details=details)