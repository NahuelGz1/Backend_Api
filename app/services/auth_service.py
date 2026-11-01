from app.repositories.auth_repository import (
    obtener_usuario_por_id,
    obtener_historial_entradas_por_usuario,
    obtener_historial_servicios_por_usuario
)
from app.utils.dates import datetime_a_string

def consultar_perfil_usuario(id_usuario: int):
    """
    Retorna la información del usuario autenticado.
    """
    usuario = obtener_usuario_por_id(id_usuario)
    if not usuario:
        raise ValueError("Usuario no encontrado", 404)
    return usuario


def consultar_historial_completo_usuario(id_usuario: int) -> dict:
    entradas_bd = obtener_historial_entradas_por_usuario(id_usuario)
    servicios_bd = obtener_historial_servicios_por_usuario(id_usuario)

    lista_entradas = []
    for fila in entradas_bd:
        lista_entradas.append({
            "id_entrada": fila["id_entrada"],
            "numero_butaca": fila["numero_butaca"],
            "codigo_qr": fila["codigo_qr"],
            "estado": fila["estado"],
            "funcion": {
                "id": fila["id_funcion"],
                "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
                "sala": fila["sala_nombre"],
                "local": fila["cine_local"]
            },
            "pelicula": {
                "titulo": fila["pelicula_titulo"],
                "poster": fila["pelicula_poster"],
                "duracion": fila["pelicula_duracion"]
            }
        })

    lista_servicios = []
    for fila in servicios_bd:
        lista_servicios.append({
            "id_compra_servicio": fila["id_compra_servicio"],
            "id_servicio": fila["id_servicio"],
            "servicio": fila["servicio_nombre"],
            "precio": float(fila["precio"]) if fila["precio"] is not None else 0.0,
            "fecha_hora_compra": datetime_a_string(fila["fecha_hora_compra"])
        })

    return {
        "entradas": lista_entradas,
        "servicios": lista_servicios
    }
