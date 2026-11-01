from flask import Blueprint, request, jsonify
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito, procesar_error_api
from app.services.auth_service import (
    consultar_perfil_usuario,
    consultar_historial_completo_usuario
)
from app.utils.security import hashear_password
from app.repositories.auth_repository import crear_usuario

auth_bp = Blueprint("auth", __name__)


# Endpoint de registro (como el prefijo en app.py será '/api/auth', la ruta final es '/api/auth/register')
@auth_bp.route("/register", methods=["POST"])
def registrar_usuario():
    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "No se recibieron datos en formato JSON"
        }), 400
    
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    if not nombre or not email or not password:
        return jsonify({
            "status": "error",
            "message": "Faltan datos obligatorios: 'nombre', 'email' y 'password' son requeridos"
        }), 400
    
    password_hash = hashear_password(password)

    resultado = crear_usuario(
        nombre=nombre,
        email=email,
        password_hash=password_hash,
        rol="cliente"
    )

    if "error" in resultado:
        return jsonify({
            "status": "error",
            "message": resultado["error"]
        }), 400
    
    return jsonify({
        "status": "success",
        "message": "Usuario registrado exitosamente",
        "data": resultado
    }), 201


@auth_bp.route("/login", methods=["POST"])
def iniciar_sesion():
    return {}


@auth_bp.route("/usuarios/me", methods=["GET"])
@requiere_autenticacion
def obtener_usuario_actual():
    try:
        id_usuario = request.usuario_actual.get("sub")
        perfil = consultar_perfil_usuario(id_usuario)
        return responder_exito(data=perfil, mensaje="Perfil obtenido con éxito", status_code=200)
    except Exception as e:
        return procesar_error_api(e)


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
@requiere_autenticacion
def obtener_historial_usuario():
    try:
        id_usuario = request.usuario_actual.get("sub")
        historial = consultar_historial_completo_usuario(id_usuario)
        return responder_exito(data=historial, mensaje="Historial obtenido con éxito", status_code=200)
    except Exception as e:
        return procesar_error_api(e)
