from app.repositories import servicios_repository as repositorio
from app.validators import servicios_validator as validador


def _servicio_a_dict(fila: dict) -> dict:
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        "precio": float(fila["precio"]),
    }


def _validar(datos: dict) -> dict:
    servicio, errores = validador.validar_servicio(datos)
    if errores:
        raise ValueError("Hay datos inválidos en la solicitud")
    return servicio


def listar_servicios() -> list:
    filas = repositorio.listar()
    return [_servicio_a_dict(fila) for fila in filas]


def obtener_servicio(servicio_id: int) -> dict:
    fila = repositorio.buscar_por_id(servicio_id)
    if fila is None:
        raise ValueError(f"No existe el servicio {servicio_id}")
    return _servicio_a_dict(fila)


def crear_servicio(datos: dict) -> dict:
    servicio = _validar(datos)
    nuevo_id = repositorio.insertar(servicio)

    servicio["id"] = nuevo_id
    servicio["precio"] = float(servicio["precio"])
    return servicio


def modificar_servicio(servicio_id: int, datos: dict) -> dict:
    obtener_servicio(servicio_id)
    servicio = _validar(datos)

    repositorio.modificar(servicio_id, servicio)

    servicio["id"] = servicio_id
    servicio["precio"] = float(servicio["precio"])
    return servicio


def eliminar_servicio(servicio_id: int) -> dict:
    obtener_servicio(servicio_id)
    repositorio.eliminar(servicio_id)
    return {"id": servicio_id}