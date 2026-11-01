from flask import Blueprint
from app.utils.decorators import requiere_administrador
from app.utils.response import responder_exito, procesar_error_api
from app.services.ocupacion_service import calcular_reporte_ocupacion

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/ocupacion", methods=["GET"])
@requiere_administrador
def obtener_metrica():
    try:
        reporte = calcular_reporte_ocupacion()
        return responder_exito(
            data=reporte,
            mensaje="Métricas de ocupación obtenidas con éxito",
            status_code=200
        )
    except Exception as e:
        return procesar_error_api(e)

