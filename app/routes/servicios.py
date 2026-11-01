
from flask import Blueprint, request

from app.services import servicios_service
from app.utils.response import responder_exito, responder_error
from app.utils.decorators import requiere_autenticacion, requiere_administrador

servicios_bp = Blueprint("servicios", __name__)


def _responder_error(error):
    """Arma la respuesta de error con el mensaje, el código y los detalles que manda el service."""
    return responder_error(
        error["mensaje"],
        error["codigo"],
        error.get("detalles")
    )


@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    """Lista todos los servicios. Endpoint público."""
    servicios = servicios_service.listar_servicios()
    return responder_exito(servicios)

@servicios_bp.route("/servicios", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def crear_servicio():
    """Crea un servicio nuevo a partir del JSON que manda el administrador."""
    datos = request.get_json(silent=True)

    if datos is None:
        return responder_error("Se requiere un JSON válido", 400)

    servicio, error = servicios_service.crear_servicio(datos)
    if error:
        return _responder_error(error)

    return responder_exito(servicio, "Servicio creado", 201)


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PUT"])
@requiere_autenticacion
@requiere_administrador
def modificar_servicio(servicio_id: int):
    """Modifica un servicio que ya existe."""
    datos = request.get_json(silent=True)

    if datos is None:
        return responder_error("Se requiere un JSON válido", 400)

    servicio, error = servicios_service.modificar_servicio(servicio_id, datos)
    if error:
        return _responder_error(error)

    return responder_exito(servicio, "Servicio modificado")


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
@requiere_autenticacion
@requiere_administrador
def desactivar_servicio(servicio_id: int):
    """Borra un servicio que ya existe."""
    resultado, error = servicios_service.eliminar_servicio(servicio_id)
    if error:
        return _responder_error(error)

    return responder_exito(resultado, "Servicio eliminado")
