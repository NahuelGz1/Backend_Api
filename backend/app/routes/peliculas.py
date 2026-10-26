from flask import Blueprint
peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    return {}


@peliculas_bp.route("/peliculas/<int:pelicula_id>", methods=["GET"])
def obtener_detalle_pelicula(pelicula_id: int):
    return {}


@peliculas_bp.route("/peliculas/buscar-externa", methods=["GET"])
def buscar_pelicula_externa():
    return {}


@peliculas_bp.route("/peliculas", methods=["POST"])
def crear_pelicula_local():
    return {}