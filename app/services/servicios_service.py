from app.repositories import servicios_repository as repositorio
from app.validators import servicios_validator as validador


def _servicio_a_dict(fila):
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        # El precio viene de la base como Decimal, lo pasamos a float para el JSON
        "precio": float(fila["precio"]),
    }


def _validar(datos):
    """Valida los datos que llegan. Devuelve (servicio, error)."""
    servicio, errores = validador.validar_servicio(datos)
    if errores:
        return None, {"mensaje": "Hay datos inválidos", "codigo": 400, "detalles": errores}

    return servicio, None


def listar_servicios():
    filas = repositorio.listar()

    servicios = []
    for fila in filas:
        servicio_dict = _servicio_a_dict(fila)
        servicios.append(servicio_dict)

    return servicios


def obtener_servicio(servicio_id):
    """Un servicio. Devuelve (servicio, error)."""
    fila = repositorio.buscar_por_id(servicio_id)
    if fila is None:
        return None, {"mensaje": f"No existe el servicio {servicio_id}", "codigo": 404}

    return _servicio_a_dict(fila), None


def crear_servicio(datos):
    """Valida los datos, guarda el servicio y lo devuelve ya creado."""
    servicio, error = _validar(datos)
    if error:
        return None, error

    nuevo_id = repositorio.insertar(servicio)
    return obtener_servicio(nuevo_id)


def modificar_servicio(servicio_id, datos):
    """Cambia los datos de un servicio que ya existe."""
    existente, error = obtener_servicio(servicio_id)
    if error:
        return None, error

    servicio, error = _validar(datos)
    if error:
        return None, error

    repositorio.modificar(servicio_id, servicio)
    return obtener_servicio(servicio_id)


def eliminar_servicio(servicio_id):
    """Borra un servicio que ya existe."""
    existente, error = obtener_servicio(servicio_id)
    if error:
        return None, error

    repositorio.eliminar(servicio_id)
    return {"id": servicio_id}, None