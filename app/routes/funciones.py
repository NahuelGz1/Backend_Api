from app.services import funciones_service
from flask import Blueprint, request
from app.utils.response import responder_exito, responder_error
from app.utils.decorators import requiere_autenticacion, requiere_administrador
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
@requiere_autenticacion
@requiere_administrador
def programar_funcion():
    """POST /funciones -> Programa una función nueva (solo administrador).

    JSON: {"id_pelicula": int, "id_sala": int, "fecha_hora_proyeccion": "YYYY-MM-DD HH:MM:SS"}
    """
    datos = request.get_json(silent=True)
    funcion = funciones_service.programar_funcion(datos)
    return responder_exito(data=funcion, message="Función programada", status_code=201)


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["PATCH"])
@requiere_autenticacion
@requiere_administrador
def modificar_funcion(funcion_id: int):
    """PATCH /funciones/<funcion_id> -> Modifica película, sala y/o fecha y hora (solo administrador).
    Se envían solo los campos que se quieren cambiar."""
    datos = request.get_json(silent=True)
    funcion = funciones_service.modificar_funcion(funcion_id, datos)
    return responder_exito(data=funcion, message="Función modificada")


@funciones_bp.route("/funciones/<int:funcion_id>", methods=["DELETE"])
@requiere_autenticacion
@requiere_administrador
def dar_baja_funcion(funcion_id: int):
    """DELETE /funciones/<funcion_id> -> Da de baja una función sin entradas (solo administrador)."""
    resultado = funciones_service.dar_baja_funcion(funcion_id)
    return responder_exito(data=resultado, message="Función dada de baja")