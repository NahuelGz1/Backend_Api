from app.repositories import compras_repository
from app.utils.constantes import ESTADO_ENTRADA_COMPRADA, ESTADO_ENTRADA_UTILIZADA

def validar_acceso(codigo_qr: str) -> dict:
    if not codigo_qr:
        raise ValueError("El código QR no puede estar vacío.")

    entrada = compras_repository.obtener_entrada_por_qr(codigo_qr)

    if not entrada:
        raise ValueError("El código QR presentado no es válido o no existe.")

    if entrada["estado"] == ESTADO_ENTRADA_UTILIZADA:
        raise ValueError("Esta entrada ya fue ingresada previamente.")

    if entrada["estado"] != ESTADO_ENTRADA_COMPRADA:
        raise ValueError(f"La entrada no está activa para ingreso (estado: {entrada['estado']}).")

    compras_repository.actualizar_estado_entrada(entrada["id_entrada"], ESTADO_ENTRADA_UTILIZADA)

    return {
        "id_entrada": entrada["id_entrada"],
        "pelicula": entrada.get("pelicula"),
        "numero_butaca": entrada.get("numero_butaca"),
        "estado_nuevo": ESTADO_ENTRADA_UTILIZADA
    }
