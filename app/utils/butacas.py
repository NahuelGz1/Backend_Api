LETRAS_FILAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BUTACAS_POR_FILA = 10


def nombre_fila(indice: int) -> str:
    return LETRAS_FILAS[indice] if indice < len(LETRAS_FILAS) else str(indice + 1)


def ubicacion_butaca(numero_butaca: int, columnas: int = BUTACAS_POR_FILA) -> tuple[str, int]:
    indice, posicion = divmod(int(numero_butaca) - 1, columnas)
    return nombre_fila(indice), posicion + 1


def etiqueta_butaca(numero_butaca: int) -> str:
    fila, numero = ubicacion_butaca(numero_butaca)
    return f"{fila}{numero}"


def lista_etiquetas_butacas(numeros_butacas: list[int]) -> list[str]:
    return [etiqueta_butaca(numero) for numero in sorted(numeros_butacas)]


def etiquetas_butacas(numeros_butacas: list[int]) -> str:
    return ", ".join(lista_etiquetas_butacas(numeros_butacas))
