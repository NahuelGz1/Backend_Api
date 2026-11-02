from flask import Blueprint, request
from app.services.compras_service import obtener_entrada_detalle, procesar_compra, cancelar_entrada_usuario, anular_compra_servicio, obtener_detalle_compra_servicio
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito, responder_error

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("/", methods=["POST"])
@requiere_autenticacion
def crear_compra_endpoint():
    datos_compra = request.get_json(silent=True) or {}
    id_usuario_peticion = request.usuario_actual.get("id") or request.usuario_actual.get("sub")
    
    respuesta, status = procesar_compra(datos_compra, id_usuario_peticion)
    if status >= 400:
        return responder_error(code=status, message=respuesta.get("error", "Error al procesar la compra"))
    
    return responder_exito(data=respuesta, message=respuesta.get("mensaje", "Compra procesada"), status_code=status)


@compras_bp.route("/<int:compra_id>", methods=["GET"])
@requiere_autenticacion
def obtener_detalle_endpoint(compra_id):
    id_usuario_peticion = request.usuario_actual.get("id") or request.usuario_actual.get("sub")
    tipo_compra = request.args.get("tipo_compra")
    
    if tipo_compra == "entrada":
        respuesta, status = obtener_entrada_detalle(compra_id, id_usuario_peticion)
    elif tipo_compra == "servicio":
        respuesta, status = obtener_detalle_compra_servicio(compra_id, id_usuario_peticion)
    else:
        return responder_error(code=400, message="Falta especificar el tipo_compra en la URL ('entrada' o 'servicio').")
        
    if status >= 400:
        return responder_error(code=status, message=respuesta.get("error", "Error al obtener detalle"))
    return responder_exito(data=respuesta.get("detalles") or respuesta.get("data"), status_code=status)


@compras_bp.route("/<int:compra_id>/cancelar", methods=["PUT"])
@requiere_autenticacion
def cancelar_compra_endpoint(compra_id):
    datos_compra = request.get_json(silent=True) or {}
    id_usuario_peticion = request.usuario_actual.get("id") or request.usuario_actual.get("sub")
    tipo_compra = datos_compra.get("tipo_compra")
    
    if tipo_compra == "entrada":
        respuesta, status = cancelar_entrada_usuario(compra_id, id_usuario_peticion)
    elif tipo_compra == "servicio":
        respuesta, status = anular_compra_servicio(compra_id, id_usuario_peticion)
    else:
        return responder_error(code=400, message="Tipo de compra inválido. Debe ser 'entrada' o 'servicio'.")
        
    if status >= 400:
        return responder_error(code=status, message=respuesta.get("error", "Error al cancelar"))
    return responder_exito(message=respuesta.get("mensaje", "Cancelación exitosa"), status_code=status)