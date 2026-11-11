from flask import Blueprint, request
from app.services.ocupacion_service import calcular_reporte_ocupacion
from app.utils.decorators import requiere_administrador
from app.utils.response import responder_exito

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/ocupacion", methods=["GET"])
@requiere_administrador
def obtener_metrica():
    reporte = calcular_reporte_ocupacion(request.args.get("complejo"))
    return responder_exito(
        data=reporte,
        message="Métricas de ocupación obtenidas con éxito",
        status_code=200
    )