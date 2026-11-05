from flask import Blueprint, request
from app.services import auth_service
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def registrar_usuario():
    datos = request.get_json(silent=True) or {}
    resultado = auth_service.registrar_usuario(
        datos.get("nombre"),
        datos.get("email"),
        datos.get("password")
    )
    return responder_exito(data=resultado, message="Usuario registrado exitosamente", status_code=201)


@auth_bp.route("/login", methods=["POST"])
def iniciar_sesion():
    datos = request.get_json(silent=True) or {}
    resultado = auth_service.autenticar_usuario(
        datos.get("email"),
        datos.get("password")
    )
    return responder_exito(data=resultado, message="Inicio de sesión exitoso", status_code=200)


@auth_bp.route("/logout", methods=["POST"])
@requiere_autenticacion
def cerrar_sesion():
    return responder_exito(data=None, message="Sesión cerrada correctamente", status_code=200)


@auth_bp.route("/usuarios/me", methods=["GET"])
@requiere_autenticacion
def obtener_usuario_actual():
    id_usuario = request.usuario_actual.get("sub")
    perfil = auth_service.consultar_perfil_usuario(id_usuario)
    return responder_exito(data=perfil, message="Perfil obtenido con éxito", status_code=200)


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
@requiere_autenticacion
def obtener_historial_usuario():
    id_usuario = request.usuario_actual.get("sub")
    historial = auth_service.consultar_historial_completo_usuario(id_usuario)
    return responder_exito(data=historial, message="Historial obtenido con éxito", status_code=200)