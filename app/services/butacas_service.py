from app.repositories.butacas_repository import consultar_butacas


def obtener_disponibilidad(funcion_id):
    """
    Calcula las butacas libres y ocupadas de una función.
    """
    datos = consultar_butacas(funcion_id)

    if datos is None:
        return None

    capacidad = datos["capacidad"]
    ocupadas = set(datos["ocupadas"])

    libres = []

    for numero in range(1, capacidad + 1):
        if numero not in ocupadas:
            libres.append(numero)

    return {
        "id_funcion": funcion_id,
        "capacidad": capacidad,
        "ocupadas": sorted(ocupadas),
        "libres": libres
    }