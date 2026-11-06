from app.repositories import salas_repository


def obtener_salas(local=None):
    return salas_repository.listar_salas(local)


def modificar_sala(sala_id, datos):
    sala_actual = salas_repository.buscar_por_id(sala_id)

    if not sala_actual:
        raise ValueError(f"No existe la sala {sala_id}")

    nombre = datos.get("nombre", sala_actual["nombre"])
    capacidad = datos.get("capacidad", sala_actual["capacidad"])
    local = datos.get("local", sala_actual["local"])

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("El nombre de la sala es obligatorio")

    if not isinstance(capacidad, int) or capacidad <= 0:
        raise ValueError("La capacidad debe ser un entero mayor a cero")

    if not isinstance(local, str) or not local.strip():
        raise ValueError("El local es obligatorio")

    salas_repository.actualizar(
        sala_id,
        nombre.strip(),
        capacidad,
        local.strip(),
    )

    return salas_repository.buscar_por_id(sala_id)