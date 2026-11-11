from app.repositories import compras_repository
from app.utils.constantes import ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_UTILIZADA

def validar_acceso(codigo_qr: str) -> dict:
    if not codigo_qr:
        raise ValueError("El código QR no puede estar vacío.")

    entradas = compras_repository.obtener_entradas_por_qr(codigo_qr)

    if not entradas:
        raise ValueError("El código QR presentado no es válido o no existe.")

    estados = {entrada["estado"] for entrada in entradas}
    if estados == {ESTADO_ENTRADA_UTILIZADA}:
        raise ValueError("Esta compra ya fue ingresada previamente.")
    if estados != {ESTADO_ENTRADA_COMPRADA}:
        raise ValueError("La compra no está activa para ingreso.")

    entrada = entradas[0]
    compras_repository.actualizar_estado_entradas_de_compra(
        entrada["id_compra"],
        ESTADO_ENTRADA_COMPRADA,
        ESTADO_ENTRADA_UTILIZADA,
    )

    #obtenemos los servicios asociados a la misma compra
    servicios_asociados = compras_repository.obtener_servicios_por_compra(entrada["id_compra"])

    return {
        "id_entrada": entrada["id_entrada"],
        "id_compra": entrada["id_compra"],
        "pelicula": entrada.get("pelicula"),
        "numero_butaca": entrada.get("numero_butaca"),
        "butacas": [entrada["numero_butaca"] for entrada in entradas],
        "fecha_hora": entrada.get("fecha_hora_proyeccion"),
        "sala": entrada.get("sala"),
        "complejo": entrada.get("local"),
        "estado_nuevo": ESTADO_ENTRADA_UTILIZADA,
        "servicios_adicionales": servicios_asociados,
    }


def validar_servicio_adicional(id_detalle: int) -> dict:
    exito = compras_repository.marcar_servicio_usado(id_detalle)
    if not exito:
        raise ValueError("El servicio adicional no existe o ya fue utilizado previamente.")

    return {"id_detalle": id_detalle, "estado": "utilizado"}