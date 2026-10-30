from flask import Blueprint
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/ocupacion", methods=["GET"])
def obtener_metrica():
    return{}
