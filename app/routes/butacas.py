from flask import Blueprint
from app.services import ocupacion_service
from app.utils.response import responder_exito

butacas_bp = Blueprint("butacas", __name__)


@butacas_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
def obtener_butacas_disponibilidad(funcion_id: int):
    """URL final: GET /api/butacas/funciones/<funcion_id>"""
    disponibilidad = ocupacion_service.obtener_estado_butacas(funcion_id)
    return responder_exito(data=disponibilidad, message="Disponibilidad obtenida con éxito", status_code=200)