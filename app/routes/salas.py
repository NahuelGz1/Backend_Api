from flask import Blueprint, request

from app.services import salas_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_error, responder_exito

salas_bp = Blueprint("salas", __name__)


@salas_bp.route("", methods=["GET"])
@requiere_autenticacion
def listar_salas():
    local = request.args.get("local")
    salas = salas_service.obtener_salas(local)

    return responder_exito(
        data=salas,
        message="Salas obtenidas exitosamente",
    )


@salas_bp.route("/<int:sala_id>", methods=["PATCH"])
@requiere_autenticacion
@requiere_administrador
def modificar_sala(sala_id):
    datos = request.get_json(silent=True) or {}

    try:
        sala = salas_service.modificar_sala(sala_id, datos)

        return responder_exito(
            data=sala,
            message="Sala modificada exitosamente",
        )
    except ValueError as error:
        return responder_error(
            code=400,
            message=str(error),
        )