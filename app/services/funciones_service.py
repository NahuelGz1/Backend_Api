from app.repositories import funciones_repository as repositorio


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