from flask import Blueprint, request, current_app
from app.services import qr_service, reserva_service
from app.utils.decorators import requiere_autenticacion, requiere_administrador, requiere_personal
from app.utils.response import responder_exito, responder_error, responder_error_de_validacion
from itsdangerous import BadData, URLSafeTimedSerializer
from app.utils.security import clave_secreta

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
        return responder_error_de_validacion(e)
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
@requiere_personal
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
@requiere_personal
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


@compras_bp.route("/reseña", methods=["POST"])
@requiere_autenticacion
def crear_resena():
    try:
        datos = request.get_json(silent=True) or {}
        id_usuario = request.usuario_actual.get("sub")
        id_pelicula = datos.get("id_pelicula")
        puntuacion = datos.get("puntuacion")
        resultado = reserva_service.registrar_puntuacion(id_usuario, id_pelicula, puntuacion)
        return responder_exito(data=resultado, message="Reseña añadida exitosamente")
    except ValueError as e:
        return responder_error_de_validacion(e)
    except PermissionError as e:
        return responder_error(message=str(e), code=403)
    except Exception as error:
        current_app.logger.error("No se pudo añadir la reseña (%s)", type(error).__name__)
        return responder_error(message="Error interno al añadir la reseña", code=500)  

@compras_bp.route("/<int:compra_id>/servicios", methods=["POST"])
@requiere_autenticacion
def agregar_servicios_a_compra(compra_id: int):
    try:
        datos = request.get_json(silent=True) or {}
        id_usuario = request.usuario_actual.get("sub")
        resultado = reserva_service.agregar_servicios_compra_existente(compra_id, datos, id_usuario)
        return responder_exito(data=resultado, message="Servicios agregados exitosamente", status_code=201)
    except ValueError as e:
        return responder_error_de_validacion(e)
    except PermissionError as e:
        return responder_error(message=str(e), code=403)
    except Exception as error:
        current_app.logger.error("No se pudieron agregar servicios a la compra (%s)", type(error).__name__)
        return responder_error(message="Error interno al agregar servicios", code=500)


@compras_bp.route("/resena/desde-mail", methods=["POST"])
def crear_resena_desde_mail():
    try:
        datos = request.get_json(silent=True) or {}
        token = datos.get("token")
        puntuacion = datos.get("puntuacion")

        if token is None:
            raise ValueError("El token es obligatorio")
        if puntuacion is None:
            raise ValueError("La puntuación es obligatoria")

        try:
            payload = URLSafeTimedSerializer(clave_secreta(), salt="resena-pelicula").loads(
                token, max_age=60 * 60 * 24 * 30
            )
        except BadData as error:
            raise ValueError("El enlace es inválido o venció") from error

        id_usuario = payload.get("id_usuario")
        id_pelicula = payload.get("id_pelicula")

        resultado = reserva_service.registrar_puntuacion(id_usuario, id_pelicula, int(puntuacion))
        return responder_exito(data=resultado, message="Reseña añadida exitosamente")
    except ValueError as e:
        return responder_error_de_validacion(e)
    except PermissionError as e:
        return responder_error(message=str(e), code=403)
    except Exception as error:
        current_app.logger.error("No se pudo añadir la reseña (%s)", type(error).__name__)
        return responder_error(message="Error interno al añadir la reseña", code=500)
      