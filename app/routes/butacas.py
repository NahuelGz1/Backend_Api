from flask import Blueprint, current_app

from app.services.butacas_service import obtener_disponibilidad
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito, responder_error


butacas_bp = Blueprint("butacas", __name__)


@butacas_bp.route("/<int:funcion_id>/butacas", methods=["GET"])
@requiere_autenticacion
def obtener_butacas_disponibilidad(funcion_id):
    """
    Devuelve la disponibilidad de butacas de una función.
    """
    try:
        disponibilidad = obtener_disponibilidad(funcion_id)

        if disponibilidad is None:
            return responder_error(
                code=404,
                message="La función solicitada no existe"
            )

        return responder_exito(
            data=disponibilidad,
            message="Disponibilidad consultada correctamente",
            status_code=200
        )

    except Exception:
        current_app.logger.exception("Error al consultar butacas")

        return responder_error(
            code=500,
            message="No se pudo consultar la disponibilidad"
        )