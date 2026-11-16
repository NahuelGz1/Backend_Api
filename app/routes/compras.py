from flask import Blueprint, request, current_app
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
        return responder_error(message=str(e), code=400)
    except Exception as error:
        current_app.logger.error("No se pudo procesar la compra (%s)", type(error).__name__)
        return responder_error(message="Error interno al procesar la compra", code=500)

@compras_bp.route("/<int:compra_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_compra(compra_id: int):
    try:
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.obtener_detalle_compra(compra_id, id_usuario)
        return responder_exito(data=resultado, message="Detalle de compra obtenido exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), code=404)
    except PermissionError as e:
        return responder_error(message=str(e), code=403)
    except Exception as e:
        return responder_error(message="Error al obtener el detalle de la compra", code=500)

@compras_bp.route("/<int:compra_id>/cancelar", methods=["PUT"])
@requiere_autenticacion
def endpoint_cancelar_compra(compra_id: int):
    try:
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.cancelar_compra(compra_id, id_usuario)
        return responder_exito(data=resultado, message="Compra cancelada exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except PermissionError as e:
        return responder_error(message=str(e), code=403)
    except Exception as e:
        return responder_error(message="Error interno al cancelar la compra", code=500)

@compras_bp.route("/qr/<path:codigo_qr>", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def consultar_qr_compra(codigo_qr: str):
    try:
        resultado = qr_service.consultar_compra(codigo_qr)
        return responder_exito(data=resultado, message="Compra consultada exitosamente")
    except LookupError as e:
        return responder_error(message=str(e), code=404)
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except Exception:
        current_app.logger.error("No se pudo consultar el código QR")
        return responder_error(message="Error al consultar el código QR", code=500)

@compras_bp.route("/validar-qr", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def validar_qr_compra():
    try:
        datos = request.get_json(silent=True) or {}
        codigo_qr = datos.get("codigo_qr")
        categoria = datos.get("categoria")
        if not codigo_qr:
            return responder_error(message="El campo 'codigo_qr' es obligatorio", code=400)
        if not categoria:
            return responder_error(message="El campo 'categoria' es obligatorio", code=400)

        resultado = qr_service.validar_canje(
            codigo_qr, categoria, datos.get("id_detalle"), datos.get("id_entrada")
        )
        return responder_exito(data=resultado, message="Canje registrado exitosamente")
    except LookupError as e:
        return responder_error(message=str(e), code=404)
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except Exception:
        current_app.logger.error("No se pudo validar el código QR")
        return responder_error(message="Error al validar el código QR", code=500)
