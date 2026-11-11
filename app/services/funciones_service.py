from datetime import datetime, timedelta, timezone

from app.repositories import funciones_repository as repositorio
from app.repositories import peliculas_repository
from app.validators import funciones_validator as validador
from app.utils.dates import datetime_a_string
from app.utils.constantes import PRECIO_ENTRADA_FIJO


def _funcion_a_dict(fila: dict) -> dict:
    return {
        "id": fila["funcion_id"],
        "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
        "activo": bool(fila.get("activo", True)),
        "eliminada": bool(fila.get("eliminada", False)),
        "pelicula_activa": bool(fila.get("pelicula_activa", True)),
        "pelicula_eliminada": bool(fila.get("pelicula_eliminada", False)),
        "precio_entrada": PRECIO_ENTRADA_FIJO,
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
    filas = repositorio.listar_funciones(incluir_inactivas)
    return [_funcion_a_dict(f) for f in filas]


def obtener_funcion_por_id(funcion_id: int) -> dict:
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if not fila:
        raise ValueError(f"No se encontró la función con ID {funcion_id}")

    funcion_dict = _funcion_a_dict(fila)
    funcion_dict["butacas_ocupadas"] = repositorio.obtener_butacas_ocupadas(funcion_id)
    return funcion_dict


def _ahora():
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _buscar_funcion_existente(funcion_id):
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if fila is None:
        raise ValueError(f"No existe la función {funcion_id}")
    return fila


def _buscar_pelicula_existente(id_pelicula):
    pelicula = peliculas_repository.buscar_por_id(id_pelicula)
    if pelicula is None:
        raise ValueError(f"No existe la película {id_pelicula}")
    if not pelicula.get("activo", True) or pelicula.get("eliminada", False):
        raise ValueError("Solo se pueden programar funciones para películas activas")
    return pelicula


def _verificar_sala_existente(id_sala):
    if repositorio.buscar_sala_por_id(id_sala) is None:
        raise ValueError(f"No existe la sala {id_sala}")


def _verificar_fecha_futura(fecha_hora):
    if fecha_hora <= _ahora():
        raise ValueError("La fecha y hora de la función tiene que ser posterior al momento actual")


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
        raise ValueError("La sala ya está ocupada en ese horario (se consideran 15 minutos de limpieza entre funciones)")


def programar_funcion(datos):
    funcion, errores = validador.validar_funcion_nueva(datos)
    if errores:
        raise ValueError("Hay datos inválidos en la solicitud")

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
        raise ValueError("Hay datos inválidos en la solicitud")

    if actual["fecha_hora_proyeccion"] <= _ahora():
        raise ValueError("No se puede modificar una función que ya se proyectó")

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["activas"]) > 0:
        raise ValueError("No se puede modificar una función con entradas vendidas")

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
    _buscar_funcion_existente(funcion_id)

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["total"]) > 0:
        raise ValueError("No se puede dar de baja una función que tiene entradas registradas")

    repositorio.eliminar_funcion(funcion_id)
    return {"id": funcion_id}


def cambiar_estado_funcion(funcion_id, activo):
    funcion = _buscar_funcion_existente(funcion_id)
    if activo:
        pelicula = peliculas_repository.buscar_por_id(funcion["pelicula_id"])
        if pelicula is None or not pelicula.get("activo", True) or pelicula.get("eliminada", False):
            raise ValueError(
                "No se puede activar la función porque la película está inactiva o fue retirada del catálogo"
            )
    repositorio.cambiar_estado_funcion(funcion_id, activo)
    return _funcion_a_dict(_buscar_funcion_existente(funcion_id))