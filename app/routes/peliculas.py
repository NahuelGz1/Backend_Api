from flask import Blueprint, request
from app.services import peliculas_service
from app.utils.decorators import requiere_administrador, requiere_autenticacion
from app.utils.response import responder_error, responder_exito

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    try:
        cartelera = peliculas_service.obtener_cartelera()
        return responder_exito(
            data=cartelera, message="Cartelera obtenida exitosamente"
        )
    except Exception as e:
        return responder_error(
            code=500, message=str(e)
        )


@peliculas_bp.route("/<int:pelicula_id>", methods=["GET"])
def obtener_detalle_pelicula(pelicula_id: int):
    try:
        pelicula = peliculas_service.obtener_pelicula(pelicula_id)
        if not pelicula:
            return responder_error(
                code=404, message="Película no encontrada"
            )
        return responder_exito(
            data=pelicula, message="Detalle de película obtenido exitosamente"
        )
    except ValueError as ve:
        # Si el servicio lanza ValueError(mensaje, status_code)
        msg = ve.args[0] if ve.args else str(ve)
        status_code = (
            ve.args[1]
            if (len(ve.args) > 1 and isinstance(ve.args[1], int))
            else 404
        )
        return responder_error(code=status_code, message=str(msg))
    except Exception as e:
        return responder_error(
            code=500, message=str(e)
        )


@peliculas_bp.route("", methods=["POST"])
@requiere_autenticacion
@requiere_administrador
def crear_pelicula_local():
    try:
        datos = request.get_json(silent=True) or {}
        pelicula = peliculas_service.crear_pelicula(datos)
        return responder_exito(
            data=pelicula, message="Película creada exitosamente", status_code=201
        )
    except ValueError as ve:
        msg = ve.args[0] if ve.args else str(ve)
        return responder_error(code=400, message=str(msg))
    except Exception as e:
        return responder_error(
            code=500, message=str(e)
        )


@peliculas_bp.route("/buscar-externa", methods=["GET"])
@requiere_autenticacion
@requiere_administrador
def buscar_pelicula_externa():
    try:
        titulo = request.args.get("titulo")
        resultados = peliculas_service.buscar_peliculas_en_tmdb(titulo)
        return responder_exito(
            data=resultados, message="Búsqueda externa realizada con éxito"
        )
    except Exception as e:
        return responder_error(
            code=400, message=str(e)
        )