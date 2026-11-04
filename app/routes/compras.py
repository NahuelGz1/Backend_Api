from flask import Blueprint, request
from app.services import qr_service, reserva_service
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("", methods=["POST"])
@requiere_autenticacion
def checkout_compra():
    datos = request.get_json(silent=True) or {}
    id_usuario = request.usuario_actual.get("sub")
    resultado = reserva_service.procesar_compra(datos, id_usuario)
    return responder_exito(data=resultado, message="Compra procesada exitosamente", status_code=201)

@compras_bp.route("/<int:compra_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_compra(compra_id: int):
    id_usuario = request.usuario_actual.get("sub")
    resultado = reserva_service.obtener_detalle_compra(compra_id, id_usuario)
    return responder_exito(data=resultado, message="Detalle de compra obtenido exitosamente")

@compras_bp.route("/<int:entrada_id>/cancelar", methods=["PUT"])
@requiere_autenticacion
def cancelar_compra(entrada_id: int):
    id_usuario = request.usuario_actual.get("sub")
    resultado = reserva_service.cancelar_entrada(entrada_id, id_usuario)
    return responder_exito(data=resultado, message="Entrada cancelada exitosamente")

@compras_bp.route("/validar-qr", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def validar_qr_compra():
    datos = request.get_json(silent=True) or {}
    resultado = qr_service.validar_acceso(datos.get("codigo_qr"))
    return responder_exito(data=resultado, message="Acceso validado y entrada utilizada")