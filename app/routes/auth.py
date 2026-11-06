from flask import Blueprint, request
from app.services import auth_service
from app.utils.decorators import requiere_autenticacion
from app.utils.response import responder_exito

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def registrar_usuario():
    datos = request.get_json(silent=True) or {}
    resultado = auth_service.registrar_usuario(
        datos.get("nombre"),
        datos.get("email"),
        datos.get("password")
    )
    return responder_exito(data=resultado, message="Usuario registrado exitosamente", status_code=201)


@auth_bp.route("/login", methods=["POST"])
def iniciar_sesion():
    datos = request.get_json(silent=True) or {}
    resultado = auth_service.autenticar_usuario(
        datos.get("email"),
        datos.get("password")
    )
    return responder_exito(data=resultado, message="Inicio de sesión exitoso", status_code=200)


@auth_bp.route("/logout", methods=["POST"])
@requiere_autenticacion
def cerrar_sesion():
    return responder_exito(data=None, message="Sesión cerrada correctamente", status_code=200)


@auth_bp.route("/usuarios/me", methods=["GET"])
@requiere_autenticacion
def obtener_usuario_actual():
    id_usuario = request.usuario_actual.get("sub")
    perfil = auth_service.consultar_perfil_usuario(id_usuario)
    return responder_exito(data=perfil, message="Perfil obtenido con éxito", status_code=200)


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
@requiere_autenticacion
def obtener_historial_usuario():
    id_usuario = request.usuario_actual.get("sub")
    historial = auth_service.consultar_historial_completo_usuario(id_usuario)
    return responder_exito(data=historial, message="Historial obtenido con éxito", status_code=200)


@auth_bp.route("/usuarios/me/perfil-completo", methods=["GET"])
@requiere_autenticacion
def obtener_perfil_completo_usuario():
    id_usuario = request.usuario_actual.get("sub")
    perfil_data = auth_service.consultar_perfil_completo_usuario(id_usuario)
    return responder_exito(
        data=perfil_data, 
        message="Perfil completo obtenido con éxito", 
        status_code=200
    )

"""@auth_bp.route("/usuarios/me/perfil-completo", methods=["GET"])
def obtener_perfil_completo_usuario():
    perfil_data = {
        "entradas_proximas": [
            {
                "pelicula": {
                    "titulo": "Inception (Origen)",
                    "poster_url": "/static/img/poster_inception.jpg",
                },
                "fecha": "2026-12-01",
                "horario": "20:00",
                "complejo": "Paradiso Centro",
                "sala": "Sala 1 3D",
                "butacas": "D5, D6",
                "cantidad_entradas": 2,
                "subtotal_entradas": "$ 12.000",
                "subtotal_servicios": "$ 8.500",
                "total": "$ 20.500",
                "codigo_operacion": "TK-98421",
            },
            {
                "pelicula": {
                    "titulo": "Dune: Parte 2",
                    "poster_url": "/static/img/poster_dune2.jpg",
                },
                "fecha": "2026-12-10",
                "horario": "22:15",
                "complejo": "Paradiso Unicenter",
                "sala": "Sala IMAX 4D",
                "butacas": "H12, H13, H14",
                "cantidad_entradas": 3,
                "subtotal_entradas": "$ 22.500",
                "subtotal_servicios": "$ 14.000",
                "total": "$ 36.500",
                "codigo_operacion": "TK-99012",
            },
            {
                "pelicula": {
                    "titulo": "Spider-Man: Across the Spider-Verse",
                    "poster_url": "/static/img/poster_spiderman.jpg",
                },
                "fecha": "2026-12-18",
                "horario": "17:30",
                "complejo": "Paradiso Belgrano",
                "sala": "Sala 3",
                "butacas": "B3",
                "cantidad_entradas": 1,
                "subtotal_entradas": "$ 6.500",
                "subtotal_servicios": "$ 0",
                "total": "$ 6.500",
                "codigo_operacion": "TK-99580",
            }
        ],
        "peliculas_vistas": [
            {
                "pelicula": {
                    "titulo": "Interstellar",
                    "poster_url": "/static/img/poster_interstellar.jpg",
                },
                "fecha": "2026-10-15",
                "horario": "18:30",
                "complejo": "Paradiso Unicenter",
                "sala": "Sala IMAX",
                "butacas": "F10",
                "cantidad_entradas": 1,
                "subtotal_entradas": "$ 7.000",
                "subtotal_servicios": "$ 0",
                "total": "$ 7.000",
                "codigo_operacion": "TK-11029",
            },
            {
                "pelicula": {
                    "titulo": "Oppenheimer",
                    "poster_url": "/static/img/poster_oppenheimer.jpg",
                },
                "fecha": "2026-08-22",
                "horario": "21:00",
                "complejo": "Paradiso Centro",
                "sala": "Sala 2",
                "butacas": "E8, E9",
                "cantidad_entradas": 2,
                "subtotal_entradas": "$ 11.000",
                "subtotal_servicios": "$ 6.000",
                "total": "$ 17.000",
                "codigo_operacion": "TK-08341",
            },
            {
                "pelicula": {
                    "titulo": "The Batman",
                    "poster_url": "/static/img/poster_batman.jpg",
                },
                "fecha": "2026-05-04",
                "horario": "19:00",
                "complejo": "Paradiso Caballito",
                "sala": "Sala 4 3D",
                "butacas": "G5",
                "cantidad_entradas": 1,
                "subtotal_entradas": "$ 5.500",
                "subtotal_servicios": "$ 3.500",
                "total": "$ 9.000",
                "codigo_operacion": "TK-04210",
            }
        ],
        "consumos_candy": [
            {
                "nombre": "Combo Duo Popcorn + 2 Bebidas Grandes",
                "cantidad": 1,
                "precio_unitario": "8.500",
                "fecha": "2026-12-01",
                "codigo_pedido": "CB-5541",
            },
            {
                "nombre": "Combo Mega Balde Popcorn XL + 3 Bebidas",
                "cantidad": 1,
                "precio_unitario": "14.000",
                "fecha": "2026-12-10",
                "codigo_pedido": "CB-6102",
            },
            {
                "nombre": "Golosinas M&M Chocolate 200g",
                "cantidad": 2,
                "precio_unitario": "3.000",
                "fecha": "2026-08-22",
                "codigo_pedido": "CB-3190",
            },
            {
                "nombre": "Nacho Supreme con Queso Cheddar",
                "cantidad": 1,
                "precio_unitario": "3.500",
                "fecha": "2026-05-04",
                "codigo_pedido": "CB-1120",
            }
        ],
        "consumos_candy_total": "32.000",
    }
    
    return responder_exito(
        data=perfil_data, 
        message="Perfil de prueba completo obtenido con éxito", 
        status_code=200
    )"""