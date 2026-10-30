"""Respuestas JSON que comparten todas las rutas del backend."""

from flask import jsonify


def respuesta_error(error):
    """Convierte el error que devuelve un service en la respuesta JSON.

    error es un diccionario como {"mensaje": "...", "codigo": 404}.
    Puede traer también "detalles" (por ejemplo, qué campo falló al validar).
    """
    # Uso .get() con un valor por defecto por si el diccionario viene incompleto
    cuerpo = {"status": "error", "message": error.get("mensaje", "Error desconocido")}
    if error.get("detalles"):
        cuerpo["details"] = error.get("detalles")
    return jsonify(cuerpo), error.get("codigo", 500)
