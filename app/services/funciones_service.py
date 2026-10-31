from app.repositories import funciones_repository as repositorio


def _funcion_a_dict(fila):
    return {
        "id": fila["funcion_id"],
        "fecha_hora_proyeccion": fila["fecha_hora_proyeccion"].isoformat(),
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
    return [f["local"] for f in filas]

def obtener_salas(local=None):
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

def obtener_funciones():
    filas = repositorio.listar_funciones()
    return [_funcion_a_dict(f) for f in filas]

def obtener_funcion_por_id(funcion_id: int):
    fila = repositorio.buscar_funcion_por_id(funcion_id)
    if not fila:
        return None
    return _funcion_a_dict(fila)