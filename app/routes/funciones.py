from app.services import funciones_service
from flask import Blueprint
from app.utils.response import responder_exito, responder_error
funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/locales", methods=["GET"])
def listar_locales():
    locales = funciones_service.obtener_locales()
    return responder_exito(locales)


@funciones_bp.route("/salas", methods=["GET"])
def listar_todas_las_salas():
    salas, error = funciones_service.obtener_salas()
    return responder_exito(salas)


@funciones_bp.route("/salas/<string:nombre_local>", methods=["GET"])
def listar_salas_por_local(nombre_local: str):
    salas, error = funciones_service.obtener_salas(local=nombre_local)
    return responder_exito(salas)


@funciones_bp.route("/funciones", methods=["GET"])
def listar_funciones():
    funciones = funciones_service.obtener_funciones()
    return responder_exito(funciones)


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
def obtener_detalle_funcion(funcion_id: int):
    funcion = funciones_service.obtener_funcion_por_id(funcion_id)
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
