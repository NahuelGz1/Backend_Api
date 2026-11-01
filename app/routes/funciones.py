from app.services import funciones_service
from flask import Blueprint
from app.utils.response import responder_exito, responder_error
from app.utils.decorators import requiere_autenticacion
funciones_bp = Blueprint("funciones", __name__)

@funciones_bp.route("/locales", methods=["GET"])
@requiere_autenticacion
def listar_locales():
    """GET /locales -> Devuelve el listado de nombres de todos los locales."""
    locales, error = funciones_service.obtener_locales()
    if error:
        return responder_error(error)
    return responder_exito(locales)


@funciones_bp.route("/salas", methods=["GET"])
@requiere_autenticacion
def listar_salas():
    """GET /salas -> Lista todas las salas. Permite filtro opcional ?local=Nombre."""
    local = request.args.get("local")
    salas, error = funciones_service.obtener_salas(local)
    if error:
        return responder_error(error)
    return responder_exito(salas)


@funciones_bp.route("/funciones", methods=["GET"])
@requiere_autenticacion
def listar_funciones():
    """GET /funciones -> Lista todas las funciones registradas."""
    funciones, error = funciones_service.obtener_funciones()
    if error:
        return responder_error(error)
    return responder_exito(funciones)


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_funcion(funcion_id: int):
    """GET /funciones/<funcion_id> -> Detalle de una función específica."""
    funcion, error = funciones_service.obtener_funcion_por_id(funcion_id)
    if error:
        return responder_error(error)
    return responder_exito(funcion)


@funciones_bp.route("/funciones", methods=["POST"])
def programar_funcion():
    return {}


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["DELETE"])
def dar_baja_funcion(funcion_id: int):
    return {}

@funciones_bp.route("/funciones/<int:funcion_id>", methods=["PATH"])
def modificar_funcion(funcion_id: int):
    return {}
