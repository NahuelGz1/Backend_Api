from flask import Blueprint
funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/locales", methods=["GET"])
def listar_locales():
    return {}


@funciones_bp.route("/salas", methods=["GET"])
def listar_salas_por_local(local_id: int):
    return {}



@funciones_bp.route("/funciones", methods=["GET"])
def listar_funciones():
    return {}


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
def obtener_detalle_funcion(funcion_id: int):
    return {}


@funciones_bp.route("/funciones", methods=["POST"])
def programar_funcion():
    return {}


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["DELETE"])
def dar_baja_funcion(funcion_id: int):
    return {}

@funciones_bp.route("/funciones/<int:funcion_id>", methods=["PATH"])
def modificar_funcion(funcion_id: int):
    return {}
