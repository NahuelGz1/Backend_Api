from flask import Blueprint
servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    return{}


@servicios_bp.route("/servicios", methods=["POST"])
def crear_servicio():
    return{}


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PUT"])
def modificar_servicio(servicio_id: int):
    return{}


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
def desactivar_servicio(servicio_id: int):
    return{}




