from flask import Blueprint
butacas_bp = Blueprint("butacas", __name__)


@butacas_bp.route("/funciones/<int:funcion_id>/butacas", methods=["GET"])
def obtener_butacas_disponibilidad(funcion_id: int):
    return {}