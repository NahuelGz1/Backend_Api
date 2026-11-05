from flask import Blueprint, request
from app.services import servicios_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_exito

servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.route("", methods=["GET"])
def listar_servicios():
    servicios = servicios_service.listar_servicios()
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