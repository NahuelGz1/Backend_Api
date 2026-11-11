from flask import Blueprint, request
from app.services import funciones_service, ocupacion_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_exito, responder_error

funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/locales", methods=["GET"])
@requiere_autenticacion
def listar_locales():
    try:
        locales = funciones_service.obtener_locales()
        return responder_exito(data=locales, message="Locales obtenidos exitosamente")
    except Exception as e:
        return responder_error(message="Error al obtener locales", code=500)


@funciones_bp.route("/salas", methods=["GET"])
@requiere_autenticacion
def listar_salas():
    try:
        local = request.args.get("local")
        salas = funciones_service.obtener_salas(local)
        return responder_exito(data=salas, message="Salas obtenidas exitosamente")
    except Exception as e:
        return responder_error(message="Error al obtener salas", code=500)


@funciones_bp.route("", methods=["GET"])
@requiere_autenticacion
def listar_funciones():
    try:
        funciones = funciones_service.obtener_funciones(
            request.args.get("incluir_inactivas") == "1"
        )
        return responder_exito(data=funciones, message="Funciones obtenidas exitosamente")
    except Exception as e:
        return responder_error(message="Error al obtener funciones", code=500)


@funciones_bp.route("/<int:funcion_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_funcion(funcion_id: int):
    try:
        funcion = funciones_service.obtener_funcion_por_id(funcion_id)
        return responder_exito(data=funcion, message="Detalle de función obtenido exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), code=404)
    except Exception as e:
        return responder_error(message="Error al obtener el detalle de la función", code=500)


@funciones_bp.route("", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def programar_funcion():
    try:
        datos = request.get_json(silent=True) or {}
        funcion = funciones_service.programar_funcion(datos)
        return responder_exito(data=funcion, message="Función programada exitosamente", status_code=201)
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except Exception as e:
        return responder_error(message="Error interno al programar la función", code=500)


@funciones_bp.route("/<int:funcion_id>", methods=["PATCH"])
@requiere_autenticacion
@requiere_administrador
def modificar_funcion(funcion_id: int):
    try:
        datos = request.get_json(silent=True) or {}
        funcion = funciones_service.modificar_funcion(funcion_id, datos)
        return responder_exito(data=funcion, message="Función modificada exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except Exception as e:
        return responder_error(message="Error interno al modificar la función", code=500)


@funciones_bp.route("/<int:funcion_id>", methods=["DELETE"])
@requiere_autenticacion
@requiere_administrador
def dar_baja_funcion(funcion_id: int):
    try:
        resultado = funciones_service.dar_baja_funcion(funcion_id)
        return responder_exito(data=resultado, message="Función dada de baja exitosamente")
    except ValueError as e:
        return responder_error(message=str(e), code=400)
    except Exception as e:
        return responder_error(message="Error interno al dar de baja la función", code=500)


@funciones_bp.route("/<int:funcion_id>/estado", methods=["PATCH"])
@requiere_autenticacion
@requiere_administrador
def cambiar_estado_funcion(funcion_id):
    datos = request.get_json(silent=True) or {}
    if not isinstance(datos.get("activo"), bool):
        return responder_error(message="El estado de la función no es válido", code=400)
    try:
        resultado = funciones_service.cambiar_estado_funcion(funcion_id, datos["activo"])
        return responder_exito(data=resultado, message="Estado de la función actualizado")
    except ValueError as error:
        return responder_error(message=str(error), code=400)


@funciones_bp.route("/<int:funcion_id>/butacas", methods=["GET"])
def obtener_butacas_disponibilidad(funcion_id: int):
    try:
        disponibilidad = ocupacion_service.obtener_estado_butacas(funcion_id)
        return responder_exito(data=disponibilidad, message="Disponibilidad obtenida con éxito")
    except ValueError as e:
        return responder_error(message=str(e), code=404)
    except Exception as e:
        return responder_error(message="Error al obtener disponibilidad de butacas", code=500)