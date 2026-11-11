from flask import Blueprint, request
from app.services import servicios_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_error, responder_exito

servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.route("", methods=["GET"])
def listar_servicios():
    incluir_inactivos = request.args.get("incluir_inactivos") == "1"
    servicios = servicios_service.listar_servicios(incluir_inactivos)
    return responder_exito(
        data=servicios,
        message="Servicios obtenidos exitosamente"
    )


@servicios_bp.route("", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def crear_servicio():
    datos = request.get_json(silent=True) or {}
    servicio = servicios_service.crear_servicio(datos)
    return responder_exito(
        data=servicio,
        message="Servicio creado exitosamente",
        status_code=201
    )


@servicios_bp.route("/<int:servicio_id>", methods=["PUT"])
@requiere_autenticacion
@requiere_administrador
def modificar_servicio(servicio_id: int):
    datos = request.get_json(silent=True) or {}
    servicio = servicios_service.modificar_servicio(servicio_id, datos)
    return responder_exito(
        data=servicio,
        message="Servicio modificado exitosamente"
    )


@servicios_bp.route("/<int:servicio_id>", methods=["DELETE"])
@requiere_autenticacion
@requiere_administrador
def desactivar_servicio(servicio_id: int):
    resultado = servicios_service.eliminar_servicio(servicio_id)
    return responder_exito(
        data=resultado,
        message="Servicio eliminado exitosamente"
    )


@servicios_bp.route("/<int:servicio_id>/estado", methods=["PATCH"])
@requiere_autenticacion
@requiere_administrador
def cambiar_estado_servicio(servicio_id: int):
    datos = request.get_json(silent=True) or {}
    activo = datos.get("activo")
    if not isinstance(activo, bool):
        return responder_error(code=400, message="El estado del servicio no es válido")
    resultado = servicios_service.cambiar_estado_servicio(servicio_id, activo)
    return responder_exito(data=resultado, message="Estado del servicio actualizado")