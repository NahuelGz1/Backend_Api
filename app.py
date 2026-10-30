import os
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BASE_URL = "/api"

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
app.register_blueprint(auth_bp, url_prefix=f"{BASE_URL}/auth")
app.register_blueprint(butacas_bp, url_prefix=f"{BASE_URL}/butacas")
app.register_blueprint(compras_bp, url_prefix=f"{BASE_URL}/compras")
app.register_blueprint(dashboard_bp, url_prefix=f"{BASE_URL}/dashboard")
# app.register_blueprint(entradas_bp, url_prefix=f"{BASE_URL}/entradas")
app.register_blueprint(funciones_bp, url_prefix=f"{BASE_URL}/funciones")
app.register_blueprint(peliculas_bp, url_prefix=f"{BASE_URL}/peliculas")
app.register_blueprint(servicios_bp, url_prefix=f"{BASE_URL}/servicios")


@app.route(f'{BASE_URL}/ping', methods=['GET'])
def ping():
    return jsonify({
        "status": "ok",
        "message": "Backend Flask running"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)