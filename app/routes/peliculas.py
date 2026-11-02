from flask import Blueprint, request
from app.services import peliculas_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_exito

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    cartelera = peliculas_service.obtener_cartelera()
    return responder_exito(
        data=cartelera,
        message="Cartelera obtenida exitosamente"
    )


@peliculas_bp.route("/<int:pelicula_id>", methods=["GET"])
def obtener_detalle_pelicula(pelicula_id: int):
    pelicula = peliculas_service.obtener_pelicula(pelicula_id)
    return responder_exito(
        data=pelicula,
        message="Detalle de película obtenido exitosamente"
    )


@peliculas_bp.route("", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def crear_pelicula_local():
    datos = request.get_json(silent=True) or {}
    pelicula = peliculas_service.crear_pelicula(datos)
    return responder_exito(
        data=pelicula,
        message="Película creada exitosamente",
        status_code=201
    )


@peliculas_bp.route("/buscar-externa", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def buscar_pelicula_externa():
    titulo = request.args.get("titulo")
    resultados = peliculas_service.buscar_peliculas_en_tmdb(titulo)
    return responder_exito(
        data=resultados,
        message="Búsqueda externa realizada con éxito"
    )