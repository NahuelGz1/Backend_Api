from flask import Blueprint, request, jsonify
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito, responder_error
from app.utils.security import hashear_password
from app.repositories.auth_repository import crear_usuario
from app.services.auth_service import (
    autenticar_usuario,
    consultar_perfil_usuario,
    consultar_historial_completo_usuario
)

auth_bp = Blueprint("auth", __name__)


# Endpoint de registro
@auth_bp.route("/register", methods=["POST"])
def registrar_usuario():
    data = request.get_json(silent=True)

    if not data:
        return responder_error(code=400, message="No se recibieron datos en formato JSON")

    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    if not nombre or not email or not password:
        return responder_error(code=400, message="Faltan datos obligatorios: 'nombre', 'email' y 'password'")

    password_hash = hashear_password(password)

    resultado = crear_usuario(
        nombre=nombre,
        email=email,
        password_hash=password_hash,
        rol="CLIENTE"
    )

    if isinstance(resultado, dict) and "error" in resultado:
        return responder_error(code=400, message=resultado["error"])

    return responder_exito(data=resultado, message="Usuario registrado exitosamente", status_code=201)


@auth_bp.route("/login", methods=["POST"])
def iniciar_sesion():
    data = request.get_json(silent=True)
    if not data:
        return responder_error(code=400, message="No se recibieron datos en formato JSON")

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return responder_error(code=400, message="Faltan datos obligatorios: 'email' y 'password'")

    try:
        resultado = autenticar_usuario(email, password)
        return responder_exito(data=resultado, message="Inicio de sesión exitoso", status_code=200)
    except ValueError as e:
        return responder_error(code=401, message=str(e))


@auth_bp.route("/logout", methods=["POST"])
@requiere_autenticacion
def cerrar_sesion():
    return responder_exito(data=None, message="Sesión cerrada correctamente", status_code=200)


@auth_bp.route("/usuarios/me", methods=["GET"])
@requiere_autenticacion
def obtener_usuario_actual():
    try:
        id_usuario = request.usuario_actual.get("sub")
        perfil = consultar_perfil_usuario(id_usuario)
        return responder_exito(data=perfil, message="Perfil obtenido con éxito", status_code=200)
    except Exception as e:
        return responder_error(code=500, message="Error al obtener perfil", details=str(e))


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
@requiere_autenticacion
def obtener_historial_usuario():
    try:
        id_usuario = request.usuario_actual.get("sub")
        historial = consultar_historial_completo_usuario(id_usuario)
        return responder_exito(data=historial, message="Historial obtenido con éxito", status_code=200)
    except Exception as e:
        return responder_error(code=500, message="Error al obtener historial", details=str(e))