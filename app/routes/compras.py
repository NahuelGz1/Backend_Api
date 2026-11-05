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
        return responder_error(message="Error interno al procesar la compra", status_code=500)

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

@compras_bp.route("/<int:entrada_id>/cancelar", methods=["PUT"])
@requiere_autenticacion
def cancelar_compra(entrada_id: int):
    try:
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.cancelar_entrada(entrada_id, id_usuario)
        return responder_exito(data=resultado, message="Entrada cancelada exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), status_code=400)
    except PermissionError as e:
        return responder_error(message=str(e), status_code=403)
    except Exception as e:
        return responder_error(message="Error al cancelar la entrada", status_code=500)

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