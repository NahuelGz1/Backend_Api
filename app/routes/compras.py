from flask import Blueprint, request
from app.services import qr_service, reserva_service
from app.utils.decorators import requiere_autenticacion, requiere_administrador
from app.utils.response import responder_exito, responder_error

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("", methods=["POST"])
@requiere_autenticacion
def checkout_compra():
    try:
        datos = request.get_json(silent=True) or {}
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.procesar_compra(datos, id_usuario)
        return responder_exito(data=resultado, message="Compra procesada exitosamente", status_code=201)
    except ValueError as e:
        return responder_error(message=str(e), status_code=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return responder_error(message=f"Error interno: {str(e)}", status_code=500)

@compras_bp.route("/<int:compra_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_compra(compra_id: int):
    try:
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.obtener_detalle_compra(compra_id, id_usuario)
        return responder_exito(data=resultado, message="Detalle de compra obtenido exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), status_code=404)
    except PermissionError as e:
        return responder_error(message=str(e), status_code=403)
    except Exception as e:
        return responder_error(message="Error al obtener el detalle de la compra", status_code=500)

@compras_bp.route("/<int:compra_id>/cancelar", methods=["PUT"])
@requiere_autenticacion
def endpoint_cancelar_compra(compra_id: int):
    try:
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.cancelar_compra(compra_id, id_usuario)
        return responder_exito(data=resultado, message="Compra cancelada exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), status_code=400)
    except PermissionError as e:
        return responder_error(message=str(e), status_code=403)
    except Exception as e:
        return responder_error(message="Error interno al cancelar la compra", status_code=500)

@compras_bp.route("/validar-qr", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def validar_qr_compra():
    try:
        datos = request.get_json(silent=True) or {}
        codigo_qr = datos.get("codigo_qr")
        if not codigo_qr:
            return responder_error(message="El campo 'codigo_qr' es obligatorio", status_code=400)

        resultado = qr_service.validar_acceso(codigo_qr)
        return responder_exito(data=resultado, message="Acceso validado y entrada utilizada")
    except ValueError as e:
        return responder_error(message=str(e), status_code=400)
    except Exception as e:
        return responder_error(message="Error al validar el código QR", status_code=500)

@compras_bp.route("/validar-servicio", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def validar_servicio_compra():
    try:
        datos = request.get_json(silent=True) or {}
        id_detalle = datos.get("id_detalle")
        if not id_detalle:
            return responder_error(message="El campo 'id_detalle' es obligatorio", status_code=400)

        resultado = qr_service.validar_servicio_adicional(id_detalle)
        return responder_exito(data=resultado, message="Servicio adicional canjeado exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), status_code=400)
    except Exception as e:
        return responder_error(message="Error al validar el servicio adicional", status_code=500)