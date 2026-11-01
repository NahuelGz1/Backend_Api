from flask import Blueprint, request, jsonify
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
def obtener_usuario_actual():
    return {}


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
def obtener_historial_usuario():
    return {}
