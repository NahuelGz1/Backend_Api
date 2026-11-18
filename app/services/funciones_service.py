from datetime import datetime, timedelta, timezone

from app.repositories import funciones_repository as repositorio
from app.repositories import peliculas_repository
from app.repositories import compras_repository
from app.validators import funciones_validator as validador
from app.utils.dates import datetime_a_string
from app.utils.constantes import (
    PRECIO_ENTRADA_FIJO,
    ESTADO_FUNCION_EN_VENTA,
    ESTADO_FUNCION_AGOTADA,
    ESTADO_FUNCION_VENTA_CERRADA,
    ESTADO_FUNCION_FINALIZADA,
    ESTADO_FUNCION_ELIMINADA,
    ESTADO_FUNCION_CANCELADA,
)


def _ahora():
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _ya_se_proyecto(fila) -> bool:
    return fila["fecha_hora_proyeccion"] <= _ahora()


def _pelicula_vigente(fila) -> bool:
    return bool(fila.get("pelicula_activa", True)) and not bool(fila.get("pelicula_eliminada", False))


def _estado_funcion(fila) -> str:
    if fila.get("eliminada"):
        return ESTADO_FUNCION_ELIMINADA
    if fila.get("cancelada"):
        return ESTADO_FUNCION_CANCELADA
    if _ya_se_proyecto(fila):
        return ESTADO_FUNCION_FINALIZADA
    if not fila.get("activo", True) or not _pelicula_vigente(fila):
        return ESTADO_FUNCION_VENTA_CERRADA
    if int(fila.get("entradas_activas") or 0) >= int(fila.get("sala_capacidad") or 0):
        return ESTADO_FUNCION_AGOTADA
    return ESTADO_FUNCION_EN_VENTA


def _funcion_a_dict(fila: dict) -> dict:
    capacidad = int(fila.get("sala_capacidad") or 0)
    vendidas = int(fila.get("entradas_activas") or 0)
    return {
        "id": fila["funcion_id"],
        "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
        "activo": bool(fila.get("activo", True)),
        "eliminada": bool(fila.get("eliminada", False)),
        "cancelada": bool(fila.get("cancelada", False)),
        "motivo_cancelacion": fila.get("motivo_cancelacion"),
        "pelicula_activa": bool(fila.get("pelicula_activa", True)),
        "pelicula_eliminada": bool(fila.get("pelicula_eliminada", False)),
        "precio_entrada": PRECIO_ENTRADA_FIJO,
        "capacidad": capacidad,
        "entradas_vendidas": vendidas,
        "butacas_libres": max(capacidad - vendidas, 0),
        "estado": _estado_funcion(fila),
        "pelicula": {
            "id": fila["pelicula_id"],
            "titulo": fila["pelicula_titulo"],
            "duracion": fila["pelicula_duracion"],
            "activa": bool(fila.get("pelicula_activa", True)),
            "eliminada": bool(fila.get("pelicula_eliminada", False)),
        },
        "sala": {
            "id": fila["sala_id"],
            "nombre": fila["sala_nombre"],
            "local": fila["sala_local"],
            "capacidad": capacidad,
        },
    }


def obtener_locales() -> list:
    filas = repositorio.listar_locales()
    return [f["local"] for f in filas]


def obtener_salas(local: str = None) -> list:
    filas = repositorio.listar_salas(local)
    return [
        {
            "id": f["id"],
            "nombre": f["nombre"],
            "capacidad": f["capacidad"],
            "local": f["local"],
        }
        for f in filas
    ]


def obtener_funciones(incluir_inactivas: bool = False) -> list:
    # el cliente solo ve las funciones que todavia no empezaron
    desde = None if incluir_inactivas else _ahora()
    filas = repositorio.listar_funciones(incluir_inactivas, desde)
    return [_funcion_a_dict(f) for f in filas]


def obtener_funcion_por_id(funcion_id: int, es_admin: bool = False) -> dict:
    # el admin ve cualquier funcion, el cliente solo las que estan a la venta
    if es_admin:
        fila = _buscar_funcion_existente(funcion_id, incluir_eliminadas=True)
    else:
        fila = verificar_funcion_vigente(funcion_id)

    funcion_dict = _funcion_a_dict(fila)
    funcion_dict["butacas_ocupadas"] = repositorio.obtener_butacas_ocupadas(funcion_id)
    return funcion_dict


def obtener_disponibilidad_estacionamiento(funcion_id: int) -> dict:
    _buscar_funcion_existente(funcion_id)
    return compras_repository.obtener_disponibilidad_estacionamiento(funcion_id)


# devuelve la funcion si todavia se pueden comprar entradas (la usan compras y el mapa de butacas)
def verificar_funcion_vigente(funcion_id) -> dict:
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    validar_funcion_vigente(fila)
    return fila


def validar_funcion_vigente(fila) -> None:
    if fila is None or fila.get("eliminada"):
        raise ValueError("La función que elegiste no existe o ya no está disponible", 404)
    if fila.get("cancelada"):
        raise ValueError("La función fue cancelada por el cine, elegí otro horario", 409)
    if _ya_se_proyecto(fila):
        raise ValueError("La función ya comenzó, no se pueden comprar entradas", 409)
    if not fila.get("activo", True) or not _pelicula_vigente(fila):
        raise ValueError("La venta de entradas para esta función está cerrada", 409)


def _buscar_funcion_existente(funcion_id, incluir_eliminadas=False):
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if fila is None or (fila.get("eliminada") and not incluir_eliminadas):
        raise ValueError(f"No existe la función {funcion_id}", 404)
    return fila


def _verificar_no_cancelada(funcion, mensaje):
    if funcion.get("cancelada"):
        raise ValueError(mensaje, 409)


def _buscar_pelicula_existente(id_pelicula):
    pelicula = peliculas_repository.buscar_por_id(id_pelicula)
    if pelicula is None:
        raise ValueError(f"No existe la película {id_pelicula}", 404)
    if not pelicula.get("activo", True) or pelicula.get("eliminada", False):
        raise ValueError("Solo se pueden programar funciones para películas activas", 409)
    return pelicula


def _verificar_sala_existente(id_sala):
    if repositorio.buscar_sala_por_id(id_sala) is None:
        raise ValueError(f"No existe la sala {id_sala}", 404)


def _verificar_fecha_futura(fecha_hora):
    if fecha_hora <= _ahora():
        raise ValueError("La fecha y hora de la función tiene que ser posterior al momento actual", 400)


def _verificar_sin_superposicion(id_sala, inicio, duracion, funcion_a_ignorar=None):
    minutos_de_limpieza = 15
    fin = inicio + timedelta(minutes=(duracion or 0) + minutos_de_limpieza)

    conflictos = []
    for otra in repositorio.listar_funciones_de_sala(id_sala):
        if otra["funcion_id"] == funcion_a_ignorar:
            continue

        otra_inicio = otra["fecha_hora_proyeccion"]
        otra_fin = otra_inicio + timedelta(minutes=(otra["pelicula_duracion"] or 0) + minutos_de_limpieza)

        if inicio < otra_fin and otra_inicio < fin:
            conflictos.append({
                "id_funcion": otra["funcion_id"],
                "pelicula": otra["pelicula_titulo"],
                "inicio": datetime_a_string(otra_inicio),
                "sala_ocupada_hasta": datetime_a_string(otra_fin),
            })

    if len(conflictos) > 0:
        raise ValueError(
            "La sala ya está ocupada en ese horario (se consideran 15 minutos de limpieza entre funciones)",
            409,
            conflictos,
        )


def programar_funcion(datos):
    funcion, errores = validador.validar_funcion_nueva(datos)
    if errores:
        raise ValueError("Hay datos inválidos en la solicitud", 400, errores)

    pelicula = _buscar_pelicula_existente(funcion["id_pelicula"])
    _verificar_sala_existente(funcion["id_sala"])
    _verificar_fecha_futura(funcion["fecha_hora_proyeccion"])
    _verificar_sin_superposicion(
        funcion["id_sala"],
        funcion["fecha_hora_proyeccion"],
        pelicula["duracion"],
    )

    nuevo_id = repositorio.insertar_funcion(
        funcion["id_pelicula"],
        funcion["id_sala"],
        funcion["fecha_hora_proyeccion"],
    )
    return _funcion_a_dict(_buscar_funcion_existente(nuevo_id))


def modificar_funcion(funcion_id, datos):
    actual = _buscar_funcion_existente(funcion_id)

    cambios, errores = validador.validar_cambios_funcion(datos)
    if errores:
        raise ValueError("Hay datos inválidos en la solicitud", 400, errores)

    _verificar_no_cancelada(actual, "No se puede modificar una función cancelada")
    if _ya_se_proyecto(actual):
        raise ValueError("No se puede modificar una función que ya se proyectó", 409)

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["activas"]) > 0:
        raise ValueError("No se puede modificar una función con entradas vendidas", 409)

    id_pelicula = cambios.get("id_pelicula", actual["pelicula_id"])
    id_sala = cambios.get("id_sala", actual["sala_id"])
    fecha_hora = cambios.get("fecha_hora_proyeccion", actual["fecha_hora_proyeccion"])

    pelicula = _buscar_pelicula_existente(id_pelicula)
    _verificar_sala_existente(id_sala)
    if "fecha_hora_proyeccion" in cambios:
        _verificar_fecha_futura(fecha_hora)
    _verificar_sin_superposicion(id_sala, fecha_hora, pelicula["duracion"], funcion_a_ignorar=funcion_id)

    repositorio.actualizar_funcion(funcion_id, id_pelicula, id_sala, fecha_hora)
    return _funcion_a_dict(_buscar_funcion_existente(funcion_id))


def dar_baja_funcion(funcion_id):
    funcion = _buscar_funcion_existente(funcion_id)

    # las funciones que ya pasaron o se cancelaron quedan en el historial (y en las estadisticas)
    _verificar_no_cancelada(funcion, "La función fue cancelada y queda en el historial, no se puede eliminar")
    if _ya_se_proyecto(funcion):
        raise ValueError("No se puede eliminar una función que ya se proyectó, queda en el historial", 409)

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["activas"]) > 0:
        raise ValueError(
            "No se puede eliminar una función con entradas vendidas. Desactivala para cerrar la venta",
            409,
        )

    repositorio.eliminar_funcion(funcion_id)
    return {"id": funcion_id}


def cambiar_estado_funcion(funcion_id, activo):
    funcion = _buscar_funcion_existente(funcion_id)
    _verificar_no_cancelada(
        funcion, "La función fue cancelada, no se puede volver a activar. Programá una función nueva"
    )
    if _ya_se_proyecto(funcion):
        raise ValueError("La función ya se proyectó, no se puede cambiar su estado", 409)

    if activo:
        pelicula = peliculas_repository.buscar_por_id(funcion["pelicula_id"])
        if pelicula is None or not pelicula.get("activo", True) or pelicula.get("eliminada", False):
            raise ValueError(
                "No se puede activar la función porque la película está inactiva o fue retirada del catálogo",
                409,
            )
    repositorio.cambiar_estado_funcion(funcion_id, activo)
    return _funcion_a_dict(_buscar_funcion_existente(funcion_id))


# chequea que se pueda cancelar la funcion (la usa la devolucion a los compradores)
def verificar_funcion_cancelable(funcion_id) -> dict:
    funcion = _buscar_funcion_existente(funcion_id)
    _verificar_no_cancelada(funcion, "La función ya fue cancelada")
    if _ya_se_proyecto(funcion):
        raise ValueError("No se puede cancelar una función que ya se proyectó", 409)
    return funcion