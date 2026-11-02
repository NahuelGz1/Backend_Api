from datetime import datetime, timedelta, timezone

from app.repositories import funciones_repository as repositorio
from app.repositories import peliculas_repository
from app.validators import funciones_validator as validador
from app.utils.dates import datetime_a_string


def _funcion_a_dict(fila: dict) -> dict:
    fecha_str = (
        fila["fecha_hora_proyeccion"].isoformat()
        if hasattr(fila["fecha_hora_proyeccion"], "isoformat")
        else str(fila["fecha_hora_proyeccion"])
    )
    return {
        "id": fila["funcion_id"],
        "fecha_hora_proyeccion": fecha_str,
        "pelicula": {
            "id": fila["pelicula_id"],
            "titulo": fila["pelicula_titulo"],
            "duracion": fila["pelicula_duracion"],
        },
        "sala": {
            "id": fila["sala_id"],
            "nombre": fila["sala_nombre"],
            "local": fila["sala_local"],
        },
    }


def obtener_locales():
    filas = repositorio.listar_locales()
    locales = [f["local"] for f in filas]
    return locales, None


def obtener_salas(local: str = None):
    filas = repositorio.listar_salas(local)
    salas = [
        {
            "id": f["id"],
            "nombre": f["nombre"],
            "capacidad": f["capacidad"],
            "local": f["local"],
        }
        for f in filas
    ]
    return salas, None


def obtener_funciones():
    filas = repositorio.listar_funciones()
    funciones = [_funcion_a_dict(f) for f in filas]
    return funciones, None


def obtener_funcion_por_id(funcion_id: int):
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if not fila:
        return None, {
            "code": 404,
            "message": f"No se encontró la función con ID {funcion_id}",
        }
    return _funcion_a_dict(fila), None


# ---------- ABM de funciones (Subtask 2.1.7) ----------
# Los errores se lanzan con ValueError(mensaje, codigo[, detalles]);
# el handler de app.py los convierte en la respuesta JSON de error.

def _ahora():
    """Hora actual de Argentina (UTC-3) sin zona horaria, para comparar con los DATETIME de la base."""
    zona_argentina = timezone(timedelta(hours=-3))
    return datetime.now(zona_argentina).replace(tzinfo=None)


def _buscar_funcion_existente(funcion_id):
    """Devuelve la fila de la función o lanza 404 si no existe."""
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if fila is None:
        raise ValueError(f"No existe la función {funcion_id}", 404)
    return fila


def _buscar_pelicula_existente(id_pelicula):
    """Devuelve la película o lanza 404 si no existe."""
    pelicula = peliculas_repository.buscar_por_id(id_pelicula)
    if pelicula is None:
        raise ValueError(f"No existe la película {id_pelicula}", 404)
    return pelicula


def _verificar_sala_existente(id_sala):
    """Lanza 404 si la sala no existe."""
    if repositorio.buscar_sala_por_id(id_sala) is None:
        raise ValueError(f"No existe la sala {id_sala}", 404)


def _verificar_fecha_futura(fecha_hora):
    """Lanza 400 si la fecha y hora no es posterior al momento actual."""
    if fecha_hora <= _ahora():
        raise ValueError(
            "La fecha y hora de la función tiene que ser posterior al momento actual",
            400,
            {"fecha_hora_proyeccion": datetime_a_string(fecha_hora)},
        )


def _verificar_sin_superposicion(id_sala, inicio, duracion, funcion_a_ignorar=None):
    """Lanza 409 si la función se pisa con otra de la misma sala.

    Cada función ocupa la sala desde su inicio hasta inicio + duración de la película
    + el tiempo de limpieza entre funciones. Dos intervalos [A, B) y [C, D) se pisan
    si A < D y C < B. En el PATCH se ignora la propia función que se está modificando.
    """
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
            f"La sala ya está ocupada en ese horario (se consideran {minutos_de_limpieza} minutos de limpieza entre funciones)",
            409,
            {"funciones_superpuestas": conflictos},
        )


def programar_funcion(datos):
    """POST /funciones: valida, revisa película, sala, fecha y superposición, y crea la función."""
    funcion, errores = validador.validar_funcion_nueva(datos)
    if errores:
        raise ValueError("Hay datos inválidos", 400, errores)

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
    """PATCH /funciones/<id>: cambia solo los campos enviados.

    No se permite modificar una función que ya se proyectó ni una que tenga
    entradas vendidas (los clientes compraron para esa película, sala y horario).
    """
    actual = _buscar_funcion_existente(funcion_id)

    cambios, errores = validador.validar_cambios_funcion(datos)
    if errores:
        raise ValueError("Hay datos inválidos", 400, errores)

    if actual["fecha_hora_proyeccion"] <= _ahora():
        raise ValueError("No se puede modificar una función que ya se proyectó", 409)

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["activas"]) > 0:
        raise ValueError(
            "No se puede modificar una función con entradas vendidas",
            409,
            {"entradas_vendidas": int(entradas["activas"])},
        )

    # Lo que no vino en el JSON se mantiene como está
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
    """DELETE /funciones/<id>: borra la función solo si no tiene entradas.

    La tabla funciones no tiene columna para baja lógica, y las entradas apuntan
    a la función con una clave foránea: si se borrara, se perdería el historial.
    """
    _buscar_funcion_existente(funcion_id)

    entradas = repositorio.contar_entradas_de_funcion(funcion_id)
    if int(entradas["total"]) > 0:
        raise ValueError(
            "No se puede dar de baja una función que tiene entradas registradas",
            409,
            {"entradas_registradas": int(entradas["total"])},
        )

    repositorio.eliminar_funcion(funcion_id)
    return {"id": funcion_id}