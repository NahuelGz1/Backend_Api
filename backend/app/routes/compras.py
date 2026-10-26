from flask import Blueprint

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("/compras", methods=["POST"])
def checkout_compra():
    return {}


@compras_bp.route("/compras/<int:compra_id>", methods=["GET"])
def obtener_detalle_compra(compra_id: int):
    return {}


@compras_bp.route("/compras/<int:compra_id>/cancelar", methods=["PUT"])
def cancelar_compra(compra_id: int):
    return {}