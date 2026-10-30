from flask import Blueprint, jsonify, request

from app.services import peliculas_service
from app.utils.respuestas import respuesta_error

# SEGURIDAD: cuando esté hecho el login, importar acá los decoradores de
# login y de rol y agregarlos donde dicen los comentarios "SEGURIDAD".

peliculas_bp = Blueprint("peliculas", __name__)


# SEGURIDAD: agregar el decorador de login
@peliculas_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    """Películas con funciones vigentes, cada una con sus funciones."""
    cartelera = peliculas_service.obtener_cartelera()
    return jsonify({"status": "ok", "data": cartelera}), 200


# SEGURIDAD: agregar el decorador de login
@peliculas_bp.route("/peliculas/<int:pelicula_id>", methods=["GET"])
def obtener_detalle_pelicula(pelicula_id: int):
    """Una película con sus funciones vigentes."""
    pelicula, error = peliculas_service.obtener_pelicula(pelicula_id)
    if error:
        return respuesta_error(error)

    return jsonify({"status": "ok", "data": pelicula}), 200


# SEGURIDAD: agregar el decorador de login y el de rol "administrador"
@peliculas_bp.route("/peliculas", methods=["POST"])
def crear_pelicula_local():
    """Crea una película nueva a partir del JSON que manda el administrador."""
    # silent=True: si el cuerpo no es un JSON válido devuelve None en vez de fallar,
    # y el validador responde con un 400 claro
    datos = request.get_json(silent=True)
    pelicula, error = peliculas_service.crear_pelicula(datos)
    if error:
        return respuesta_error(error)

    return jsonify({"status": "ok", "data": pelicula}), 201


# SEGURIDAD: agregar el decorador de login y el de rol "administrador"
@peliculas_bp.route("/peliculas/buscar-externa", methods=["GET"])
def buscar_pelicula_externa():
    """Busca películas por título en TMDB (?titulo=...)."""
    resultados, error = peliculas_service.buscar_peliculas_en_tmdb(request.args.get("titulo"))
    if error:
        return respuesta_error(error)

    return jsonify({"status": "ok", "data": resultados}), 200