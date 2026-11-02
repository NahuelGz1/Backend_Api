import os
from dotenv import load_dotenv
from flask import Flask
from app.utils.response import responder_error, responder_exito

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'clave_dev_secreta')
base_url = os.getenv('API_BASE_URL', '/api')

from app.routes.auth import auth_bp
from app.routes.butacas import butacas_bp
from app.routes.compras import compras_bp
from app.routes.dashboard import dashboard_bp
from app.routes.funciones import funciones_bp
from app.routes.peliculas import peliculas_bp
from app.routes.servicios import servicios_bp

app.register_blueprint(auth_bp, url_prefix=f"{base_url}/auth")
app.register_blueprint(butacas_bp, url_prefix=f"{base_url}/butacas")
app.register_blueprint(compras_bp, url_prefix=f"{base_url}/compras")
app.register_blueprint(dashboard_bp, url_prefix=f"{base_url}/dashboard")
app.register_blueprint(funciones_bp, url_prefix=f"{base_url}/funciones")
app.register_blueprint(peliculas_bp, url_prefix=f"{base_url}/peliculas")
app.register_blueprint(servicios_bp, url_prefix=f"{base_url}/servicios")


@app.route(f'{base_url}/ping', methods=['GET'])
def ping():
    return responder_exito(data=None, message="Backend Flask running", status_code=200)


@app.errorhandler(404)
def handle_404_error(error):
    return responder_error(
        code=404,
        message="La ruta solicitada no existe en el servidor",
        details=None
    )


@app.errorhandler(ValueError)
def handle_value_error(error):
    mensaje = error.args[0] if len(error.args) > 0 else "Error de validación"
    status_code = error.args[1] if len(error.args) > 1 and isinstance(error.args[1], int) else 400
    detalles = error.args[2] if len(error.args) > 2 else None

    return responder_error(
        code=status_code,
        message=str(mensaje),
        details=detalles
    )


@app.errorhandler(PermissionError)
def handle_permission_error(error):
    mensaje = error.args[0] if len(error.args) > 0 else "Acceso no autorizado"
    return responder_error(
        code=403,
        message=str(mensaje),
        details=None
    )


@app.errorhandler(Exception)
def handle_global_exception(error):
    print(f"[ERROR INESPERADO]: {error}")
    return responder_error(
        code=500,
        message="Ocurrió un error interno en el servidor",
        details=None
    )


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)