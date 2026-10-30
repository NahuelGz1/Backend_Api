from flask import jsonify

# formateador de errores
def construir_error_api(code: str = None, message: str = None, description: str = None, level: str = 'error', errores_multiples: list = None) -> dict:
    if errores_multiples is not None:
        return {"errors": errores_multiples}
    return {
        'errors': [{
            'code': code,
            'message': message,
            'level': level,
            'description': description
        }]
    }

def procesar_error_api(error: Exception):
    if isinstance(error, ValueError):
        status = error.args[1] if len(error.args) > 1 else 400
        return error.args[0], status

    print(f"Error inesperado: {error}")
    payload = construir_error_api(
        code="internal_error",
        message="Ocurrió un error inesperado en el servidor",
        description=str(error)
    )
    return payload, 500


# respuestas http estandar
def responder_exito(data=None, mensaje="Operación exitosa", status_code=200):
    body = {"estado": "éxito", "mensaje": mensaje}
    if data is not None:
        body["datos"] = data
    return jsonify(body), status_code

def responder_error(mensaje="Error procesando la solicitud", status_code=400, detalle=None):
    body = {"estado": "error", "mensaje": mensaje}
    if detalle:
        body["detalle"] = detalle
    return jsonify(body), status_code