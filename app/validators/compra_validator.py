from decimal import Decimal, InvalidOperation


def validar_servicios_compra(servicios):
    if not isinstance(servicios, list):
        raise ValueError("Los servicios deben ser una lista.", 400)
    normalizados = []
    for servicio in servicios:
        if not isinstance(servicio, dict):
            raise ValueError("Cada servicio debe ser un objeto.", 400)
        normalizado = servicio.copy()
        for campo in ("id_servicio", "cantidad"):
            valor = servicio.get(campo)
            if isinstance(valor, str) and valor.isascii() and valor.isdigit():
                valor = int(valor)
            if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
                raise ValueError(f"El campo '{campo}' debe ser un entero positivo.", 400)
            normalizado[campo] = valor
        if "precio" not in servicio:
            raise ValueError("El precio del servicio es obligatorio.", 400)
        try:
            precio = Decimal(str(servicio["precio"]))
        except (InvalidOperation, ValueError):
            raise ValueError("El precio del servicio no es válido.", 400)
        if not precio.is_finite() or precio < 0:
            raise ValueError("El precio del servicio no es válido.", 400)
        normalizado["precio"] = precio
        normalizados.append(normalizado)
    return normalizados


def validar_cupo_estacionamiento(cantidad, cantidad_entradas, disponibles):
    if cantidad > cantidad_entradas:
        raise ValueError("La cantidad de estacionamientos no puede superar la cantidad de entradas.", 400)
    if cantidad > disponibles:
        raise ValueError(
            f"No hay suficientes espacios de estacionamiento disponibles para esta función. Quedan {disponibles} lugares.",
            400,
        )
