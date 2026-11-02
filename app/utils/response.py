from flask import jsonify


def responder_exito(data=None, message: str = "Operación exitosa", status_code: int = 200):
    """Retorna una respuesta estandarizada de éxito JSON."""
    body = {
        "ok": True,
        "data": data,
        "message": message
    }
    return jsonify(body), status_code


def responder_error(code: int = 400, message: str = "Error procesando la solicitud", details=None):
    """Retorna una respuesta estandarizada de error JSON."""
    body = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }
    return jsonify(body), code