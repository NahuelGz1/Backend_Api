import os

from dotenv import load_dotenv
from flask import Flask, request
from werkzeug.exceptions import HTTPException

from app.utils.response import responder_error, responder_exito
from db import asegurar_esquema, cargar_fixture_qr_prueba

load_dotenv()

# Usa DB_USER/DB_PASSWORD del entorno; no requiere ni ejecuta privilegios de root.
if os.getenv("AUTO_MIGRATE", "true").lower() == "true":
    asegurar_esquema()
if os.getenv("AUTO_SEED", "false").lower() == "true":
    cargar_fixture_qr_prueba()

app = Flask(__name__)
app.config.from_mapping(
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    SUPER_ADMIN_EMAIL=os.getenv("SUPER_ADMIN_EMAIL", "cine_paradiso@admin.com").strip().lower(),
    PASSWORD_RESET_URL=os.getenv("PASSWORD_RESET_URL", "http://localhost:3000/auth/restablecer-contrasena"),
    PASSWORD_RESET_MAX_AGE=1800,
    SMTP_HOST=os.getenv("SMTP_HOST", "localhost"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", "1025")),
    SMTP_FROM=os.getenv("SMTP_FROM", "no-reply@cine-paradiso.local"),
    SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
    SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
    SMTP_STARTTLS=os.getenv("SMTP_STARTTLS", "true").lower() == "true",
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)
if not app.config["JWT_SECRET_KEY"] or len(app.config["JWT_SECRET_KEY"]) < 32:
    raise RuntimeError("Configurá JWT_SECRET_KEY con al menos 32 caracteres")

base_url = os.getenv("API_BASE_URL", "/api")

from app.routes.auth import auth_bp
from app.routes.butacas import butacas_bp
from app.routes.compras import compras_bp
from app.routes.dashboard import dashboard_bp
from app.routes.funciones import funciones_bp
from app.routes.peliculas import peliculas_bp
from app.routes.servicios import servicios_bp
from app.routes.salas import salas_bp

app.register_blueprint(salas_bp, url_prefix=f"{base_url}/funciones/salas")
app.register_blueprint(auth_bp, url_prefix=f"{base_url}/auth")
app.register_blueprint(butacas_bp, url_prefix=f"{base_url}/butacas")
app.register_blueprint(compras_bp, url_prefix=f"{base_url}/compras")
app.register_blueprint(dashboard_bp, url_prefix=f"{base_url}/dashboard")
app.register_blueprint(funciones_bp, url_prefix=f"{base_url}/funciones")
app.register_blueprint(peliculas_bp, url_prefix=f"{base_url}/peliculas")
app.register_blueprint(servicios_bp, url_prefix=f"{base_url}/servicios")


@app.route(f"{base_url}/ping", methods=["GET"])
def ping():
    return responder_exito(data=None, message="Backend Flask running", status_code=200)


@app.errorhandler(404)
def handle_404_error(error):
    return responder_error(
        code=404,
        message="La ruta solicitada no existe en el servidor",
        details=None,
    )


@app.errorhandler(ValueError)
def handle_value_error(error):
    mensaje = error.args[0] if error.args else "Error de validación"
    status_code = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else 400
    detalles = error.args[2] if len(error.args) > 2 else None
    return responder_error(code=status_code, message=str(mensaje), details=detalles)


@app.errorhandler(PermissionError)
def handle_permission_error(error):
    return responder_error(code=403, message=str(error))


@app.errorhandler(HTTPException)
def handle_http_error(error):
    return responder_error(code=error.code, message=error.name)


@app.errorhandler(Exception)
def handle_global_exception(error):
    # No registrar parametros SQL, credenciales ni tokens en excepciones.
    app.logger.error("Error interno de tipo %s", type(error).__name__)
    return responder_error(code=500, message="Ocurrió un error interno en el servidor")


@app.after_request
def privacidad(response):
    if request.blueprint == "auth":
        response.headers["Cache-Control"] = "no-store"
    return response


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
