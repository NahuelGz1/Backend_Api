from flask import Blueprint, request

from app.services import peliculas_service
from app.utils.response import responder_exito
from app.utils.decorators import requiere_autenticacion, requiere_administrador

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    """Películas con funciones vigentes, cada una con sus funciones."""
    cartelera = peliculas_service.obtener_cartelera()
    return responder_exito(cartelera)


@peliculas_bp.route("/peliculas/<int:pelicula_id>", methods=["GET"])
def obtener_detalle_pelicula(pelicula_id: int):
    """Una película con sus funciones vigentes."""
    pelicula = peliculas_service.obtener_pelicula(pelicula_id)
    return responder_exito(pelicula)


@peliculas_bp.route("/peliculas", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def crear_pelicula_local():
    """Crea una película nueva a partir del JSON que manda el administrador."""
    datos = request.get_json(silent=True)
    pelicula = peliculas_service.crear_pelicula(datos)
    return responder_exito(data=pelicula, message="Película creada", status_code=201)


@peliculas_bp.route("/peliculas/buscar-externa", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def buscar_pelicula_externa():
    """Busca películas por título en TMDB (?titulo=...)."""
    resultados = peliculas_service.buscar_peliculas_en_tmdb(request.args.get("titulo"))
    return responder_exito(resultados)
