from flask import Blueprint, request, send_file
from io import BytesIO
from datetime import datetime
import re
from app.services.ocupacion_service import calcular_reporte_ocupacion
from app.services.pdf_service import generar_reporte_ventas_pdf
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


@dashboard_bp.route("/ocupacion/pdf", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def exportar_reporte_pdf():
    periodo_texto = request.args.get("periodo", "").strip()
    periodo = None
    if periodo_texto:
        try:
            inicio = datetime.strptime(periodo_texto, "%Y-%m")
        except ValueError:
            return responder_error(message="El período debe tener formato AAAA-MM.")
        if inicio.month == 12:
            fin = datetime(inicio.year + 1, 1, 1)
        else:
            fin = datetime(inicio.year, inicio.month + 1, 1)
        periodo = (inicio, fin)

    complejo = request.args.get("complejo", "").strip() or None
    reporte = calcular_reporte_ocupacion(complejo, periodo)
    pdf = generar_reporte_ventas_pdf(reporte, complejo=complejo, periodo=periodo_texto)

    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte-ventas-cine-paradiso.pdf",
    )