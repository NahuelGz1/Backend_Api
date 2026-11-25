from app.repositories import salas_repository
from app.services.funciones_service import _ahora


def obtener_salas(local=None):
    return salas_repository.listar_salas(local)


def crear_sala(datos):
    nombre = datos.get("nombre")
    capacidad = datos.get("capacidad")
    local = datos.get("local")

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre de la sala es obligatorio")

    if not isinstance(capacidad, int) or capacidad <= 0:
        raise ValueError("La capacidad debe ser un entero mayor a cero")

    if not isinstance(local, str) or not local.strip():
        raise ValueError("El local es obligatorio")

    nuevo_id = salas_repository.crear(
        nombre.strip(),
        capacidad,
        local.strip(),
    )

    return salas_repository.buscar_por_id(nuevo_id)


def modificar_sala(sala_id, datos):
    sala_actual = salas_repository.buscar_por_id(sala_id)

    if not sala_actual:
        raise ValueError(f"No existe la sala {sala_id}")

    activo = datos.get("activo")
    if "activo" in datos and not isinstance(activo, bool):
        raise ValueError("El estado de mantenimiento debe ser verdadero o falso")

    nombre = datos.get("nombre", sala_actual["nombre"])
    capacidad = datos.get("capacidad", sala_actual["capacidad"])
    local = datos.get("local", sala_actual["local"])

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre de la sala es obligatorio")

    if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
        raise ValueError("La capacidad debe ser un entero mayor a cero")

    if not isinstance(local, str) or not local.strip():
        raise ValueError("El local es obligatorio")

    salas_repository.actualizar(
        sala_id,
        nombre.strip() if "nombre" in datos else None,
        capacidad if "capacidad" in datos else None,
        local.strip() if "local" in datos else None,
        activo,
        _ahora(),
    )

    return salas_repository.buscar_por_id(sala_id)
