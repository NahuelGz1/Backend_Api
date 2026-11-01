from flask import jsonify

def responder_exito(data=None, message="Operación exitosa", status_code=200):
    """Formato de respuesta exitosa según agents.md"""
    body = {
        "ok": True,
        "data": data,
        "message": message
    }
    return jsonify(body), status_code

def responder_error(code=400, message="Error procesando la solicitud", details=None):
    """Formato de respuesta de error según agents.md"""
    body = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }
    return jsonify(body), code