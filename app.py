import os
from flask import Flask
from dotenv import load_dotenv
from app.utils.response import responder_exito, responder_error

load_dotenv()

app = Flask(__name__)

# configuración desde variables de entorno
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'clave_dev_secreta')
base_url = os.getenv('API_BASE_URL', '/api')

# Importación de Blueprints
from app.routes.auth import auth_bp
from app.routes.butacas import butacas_bp
from app.routes.compras import compras_bp
from app.routes.dashboard import dashboard_bp
# from app.routes.entradas import entradas_bp
from app.routes.funciones import funciones_bp
from app.routes.peliculas import peliculas_bp
from app.routes.servicios import servicios_bp

# Registro de Blueprints
app.register_blueprint(auth_bp, url_prefix=f"{base_url}/auth")
app.register_blueprint(butacas_bp, url_prefix=f"{base_url}/butacas")
app.register_blueprint(compras_bp, url_prefix=f"{base_url}/compras")
app.register_blueprint(dashboard_bp, url_prefix=f"{base_url}/dashboard")
# app.register_blueprint(entradas_bp, url_prefix=f"{base_url}/entradas")
app.register_blueprint(funciones_bp, url_prefix=f"{base_url}/funciones")
app.register_blueprint(peliculas_bp, url_prefix=base_url)
app.register_blueprint(servicios_bp, url_prefix=f"{base_url}/servicios")


@app.route(f'{base_url}/ping', methods=['GET'])
def ping():
    return responder_exito(data=None, message="Backend Flask running", status_code=200)


# handler global de errores inesperados
@app.errorhandler(Exception)
def handle_global_exception(error):
    # imprime el error detallado solo en la consola del servidor para depuración
    print(f"[ERROR INESPERADO]: {error}")

    # retorna una respuesta 500 estandarizada sin exponer detalles de la base de datos o del sistema
    return responder_error(
        code=500,
        message="Ocurrió un error interno en el servidor",
        details=None
    )


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)