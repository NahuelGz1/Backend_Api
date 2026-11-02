from flask import Blueprint, request, jsonify
from app.services.compras_service import obtener_entradas_por_id, procesar_compra, cancelar_entrada_usuario, anular_compra_servicio, obtener_detalle_compra_servicio

compras_bp = Blueprint("compras", __name__)

@compras_bp.route("/", methods=["POST"])
def crear_compra_endpoint():

    datos_compra = request.get_json()
    id_usuario_peticion = 1 # Hardcodeado temporalmente
    
    respuesta, status = procesar_compra(datos_compra, id_usuario_peticion)
    return jsonify(respuesta), status


@compras_bp.route("/<int:compra_id>", methods=["GET"])
def obtener_detalle_endpoint(compra_id):
    id_usuario_peticion = 1
    tipo_compra = request.args.get("tipo_compra")
    
    if tipo_compra == "entrada":
        respuesta, status = obtener_entradas_por_id(compra_id, id_usuario_peticion)
    elif tipo_compra == "servicio":
        respuesta, status = obtener_detalle_compra_servicio(compra_id, id_usuario_peticion)
    else:
        return jsonify({"error": "Falta especificar el tipo_compra en la URL."}), 400
        
    return jsonify(respuesta), status


@compras_bp.route("/<int:compra_id>/cancelar", methods=["PUT"])
def cancelar_compra_endpoint(compra_id):
    datos_compra = request.get_json()
    id_usuario_peticion = 1
    tipo_compra = datos_compra.get("tipo_compra")
    
    if tipo_compra == "entrada":
        respuesta, status = cancelar_entrada_usuario(compra_id, id_usuario_peticion)
    elif tipo_compra == "servicio":
        respuesta, status = anular_compra_servicio(compra_id, id_usuario_peticion)
    else:
        return jsonify({"error": "Tipo de compra inválido."}), 400
        
    return jsonify(respuesta), status