from flask import Blueprint, request
from datetime import datetime
import re
from app.services.ocupacion_service import calcular_reporte_ocupacion
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_exito, responder_error

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/ocupacion", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def obtener_metrica():
    periodo_texto = request.args.get("periodo", "")
    periodo = None
    if periodo_texto:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo_texto):
            return responder_error(message="El período debe tener formato AAAA-MM.")
        anio, mes = map(int, periodo_texto.split("-"))
        if anio < 1 or (anio == 9999 and mes == 12):
            return responder_error(message="El período está fuera de rango.")
        inicio = datetime(anio, mes, 1)
        fin = datetime(anio + (mes == 12), 1 if mes == 12 else mes + 1, 1)
        periodo = (inicio, fin)
    reporte = calcular_reporte_ocupacion(request.args.get("complejo"), periodo)
    return responder_exito(
        data=reporte,
        message="Métricas de ocupación obtenidas con éxito",
        status_code=200
    )