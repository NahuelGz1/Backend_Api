
import os

from dotenv import load_dotenv
from flask import Flask, request
from werkzeug.exceptions import HTTPException

from app.utils.response import responder_error, responder_exito


def create_app(config=None):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        PASSWORD_RESET_URL=os.getenv("PASSWORD_RESET_URL", "http://localhost:3000/auth/restablecer-contrasena"),
        PASSWORD_RESET_MAX_AGE=1800,
        SMTP_HOST=os.getenv("SMTP_HOST", "localhost"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "1025")),
        SMTP_FROM=os.getenv("SMTP_FROM", "no-reply@cine-paradiso.local"),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        SMTP_STARTTLS=os.getenv("SMTP_STARTTLS", "true").lower() == "true",
        MAX_CONTENT_LENGTH=16384,
    )
    if config:
        app.config.update(config)
    if not app.config["JWT_SECRET_KEY"] or len(app.config["JWT_SECRET_KEY"]) < 32:
        raise RuntimeError("Configurá JWT_SECRET_KEY con al menos 32 caracteres")

    from app.routes.auth import auth_bp
    from app.routes.butacas import butacas_bp
    from app.routes.compras import compras_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.funciones import funciones_bp
    from app.routes.peliculas import peliculas_bp
    from app.routes.servicios import servicios_bp

    base = os.getenv("API_BASE_URL", "/api")
    for blueprint, ruta in (
        (auth_bp, "auth"), (butacas_bp, "butacas"), (compras_bp, "compras"),
        (dashboard_bp, "dashboard"), (funciones_bp, "funciones"),
        (peliculas_bp, "peliculas"), (servicios_bp, "servicios"),
    ):
        app.register_blueprint(blueprint, url_prefix=f"{base}/{ruta}")

    @app.get(f"{base}/ping")
    def ping():
        return responder_exito(message="Backend Flask running")

    @app.errorhandler(ValueError)
    def validacion(error):
        codigo = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else 400
        return responder_error(code=codigo, message=str(error.args[0]))

    @app.errorhandler(PermissionError)
    def permiso(error):
        return responder_error(code=403, message=str(error))

    @app.errorhandler(HTTPException)
    def http_error(error):
        return responder_error(code=error.code, message=error.name)

    @app.errorhandler(Exception)
    def inesperado(error):
        # No registrar parametros SQL, credenciales ni tokens en excepciones.
        app.logger.error("Error interno de tipo %s", type(error).__name__)
        return responder_error(code=500, message="Ocurrió un error interno en el servidor")

    @app.after_request
    def privacidad(response):
        if request.blueprint == "auth":
            response.headers["Cache-Control"] = "no-store"
        return response

    return app
