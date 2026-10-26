from flask import Blueprint
dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/ocupacion-funcion", methods=["GET"])
def metrica_ocupacion_por_funcion():
    return{}


@dashboard_bp.route("/ventas-genero", methods=["GET"])
def metrica_ventas_por_genero():
    return {}


@dashboard_bp.route("/franjas-horarias", methods=["GET"])
def metrica_franjas_horarias():
    return{}


@dashboard_bp.route("/cancelaciones", methods=["GET"])
def metrica_compras_canceladas():
    return{}
