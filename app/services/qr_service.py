from datetime import datetime, timedelta

from itsdangerous import URLSafeTimedSerializer
from app.services.email_service import enviar_correo_resena
from app.utils.security import clave_secreta
from app.repositories import compras_repository
from app.utils.butacas import etiqueta_butaca
from app.utils.dates import FORMATO_FECHA_HORA_LEGIBLE, ahora_argentina
from app.utils.constantes import (
    CATEGORIA_ENTRADAS,
    CATEGORIA_ESTACIONAMIENTO,
    CATEGORIA_SERVICIOS,
    CATEGORIA_VIP,
    CATEGORIAS_VALIDACION,
    ESTADO_ENTRADA_CANCELADA,
    ESTADO_ENTRADA_COMPRADA,
    ESTADO_ENTRADA_UTILIZADA,
    ESTADO_VALIDACION_FUNCION_ANTICIPADA,
    ESTADO_VALIDACION_FUNCION_VENCIDA,
    ESTADO_VALIDACION_VALIDA,
    HORAS_VENTANA_QR,
)

NOMBRES_CATEGORIA = {
    CATEGORIA_ENTRADAS: "Entradas",
    CATEGORIA_VIP: "Acceso VIP",
    CATEGORIA_SERVICIOS: "Servicios",
    CATEGORIA_ESTACIONAMIENTO: "Estacionamiento",
}

MENSAJES_YA_CANJEADO = {
    CATEGORIA_VIP: "Los accesos VIP de esta compra ya fueron canjeados previamente.",
    CATEGORIA_SERVICIOS: "Los servicios de esta compra ya fueron canjeados previamente.",
    CATEGORIA_ESTACIONAMIENTO: "Todos los espacios de estacionamiento ya fueron canjeados.",
}


def categoria_de_servicio(nombre: str) -> str:
    nombre = (nombre or "").lower()
    if "estacionamiento" in nombre:
        return CATEGORIA_ESTACIONAMIENTO
    if "vip" in nombre:
        return CATEGORIA_VIP
    return CATEGORIA_SERVICIOS


def _cargar_compra(codigo_qr: str) -> tuple[dict, list[dict], list[dict]]:
    if not codigo_qr or not str(codigo_qr).strip():
        raise ValueError("El código QR no puede estar vacío.")

    entradas = compras_repository.obtener_entradas_por_qr(codigo_qr)
    if not entradas:
        raise LookupError("El código QR presentado no es válido o no existe.")

    id_compra = entradas[0]["id_compra"]
    servicios = compras_repository.obtener_servicios_por_compra(id_compra)
    return entradas[0], entradas, servicios


def _compra_cancelada(entradas: list[dict]) -> bool:
    return all(e["estado"] == ESTADO_ENTRADA_CANCELADA for e in entradas)


def _resumen_entradas(entradas: list[dict]) -> dict:
    items = [
        {
            "id": e["id_entrada"],
            "descripcion": f"Butaca {etiqueta_butaca(e['numero_butaca'])}",
            "numero_butaca": e["numero_butaca"],
            "estado": e["estado"],
        }
        for e in sorted(entradas, key=lambda e: e["numero_butaca"])
    ]
    validas = [e for e in entradas if e["estado"] != ESTADO_ENTRADA_CANCELADA]
    utilizadas = sum(1 for e in validas if e["estado"] == ESTADO_ENTRADA_UTILIZADA)
    return {
        "total": len(validas),
        "utilizados": utilizadas,
        "pendientes": len(validas) - utilizadas,
        "cancelada": not validas,
        "items": items,
    }


def _resumen_servicios(servicios: list[dict], categoria: str, cancelada: bool) -> dict:
    del_grupo = [s for s in servicios if categoria_de_servicio(s["nombre"]) == categoria]
    items = []
    for s in del_grupo:
        cantidad = int(s["cantidad"] or 0)
        usadas = min(int(s.get("cantidad_usada") or 0), cantidad)
        items.append({
            "id": s["id_detalle"],
            "id_detalle": s["id_detalle"],
            "nombre": s["nombre"],
            "cantidad": cantidad,
            "cantidad_usada": usadas,
            "pendientes": cantidad - usadas,
        })
    total = sum(i["cantidad"] for i in items)
    utilizados = sum(i["cantidad_usada"] for i in items)
    return {
        "total": total,
        "utilizados": utilizados,
        "pendientes": total - utilizados,
        "cancelada": cancelada and total > 0,
        "items": items,
    }


def _evaluar_ventana(fecha_funcion) -> tuple[str, str | None]:
    """Devuelve (estado_validacion, mensaje) según la ventana de ±HORAS_VENTANA_QR respecto a la función."""
    if not isinstance(fecha_funcion, datetime):
        return ESTADO_VALIDACION_VALIDA, None

    margen = timedelta(hours=HORAS_VENTANA_QR)
    ahora = ahora_argentina()
    programada = fecha_funcion.strftime(FORMATO_FECHA_HORA_LEGIBLE)
    if ahora < fecha_funcion - margen:
        return ESTADO_VALIDACION_FUNCION_ANTICIPADA, (
            f"La función aún no está habilitada para el ingreso. Está programada para el {programada} "
            f"y el QR se puede validar desde {HORAS_VENTANA_QR} horas antes."
        )
    if ahora > fecha_funcion + margen:
        return ESTADO_VALIDACION_FUNCION_VENCIDA, (
            f"La función del {programada} ya finalizó: el QR está fuera de la ventana de ingreso permitida."
        )
    return ESTADO_VALIDACION_VALIDA, None


def _armar_resumen(codigo_qr: str, primera: dict, entradas: list[dict], servicios: list[dict]) -> dict:
    cancelada = _compra_cancelada(entradas)
    categorias = {CATEGORIA_ENTRADAS: _resumen_entradas(entradas)}
    for categoria in (CATEGORIA_VIP, CATEGORIA_SERVICIOS, CATEGORIA_ESTACIONAMIENTO):
        categorias[categoria] = _resumen_servicios(servicios, categoria, cancelada)

    estado_validacion, mensaje_validacion = _evaluar_ventana(primera.get("fecha_hora_proyeccion"))
    return {
        "id_compra": primera["id_compra"],
        "codigo_qr": codigo_qr,
        "pelicula": primera.get("pelicula"),
        "fecha_hora": primera.get("fecha_hora_proyeccion"),
        "sala": primera.get("sala"),
        "complejo": primera.get("local"),
        "butacas": [e["numero_butaca"] for e in entradas if e["estado"] != ESTADO_ENTRADA_CANCELADA],
        "compra_cancelada": cancelada,
        "valida": estado_validacion == ESTADO_VALIDACION_VALIDA,
        "estado_validacion": estado_validacion,
        "mensaje_validacion": mensaje_validacion,
        "categorias": categorias,
    }


def consultar_compra(codigo_qr: str) -> dict:
    primera, entradas, servicios = _cargar_compra(codigo_qr)
    return _armar_resumen(codigo_qr, primera, entradas, servicios)


def _validar_una_entrada(id_compra: int, entradas: list[dict], id_entrada) -> int:
    resumen = _resumen_entradas(entradas)
    if resumen["cancelada"]:
        raise ValueError("La compra está cancelada: sus entradas no son válidas para el ingreso.")
    if resumen["pendientes"] == 0:
        raise ValueError("Las entradas de esta compra ya fueron canjeadas previamente.")

    if id_entrada is None:
        elegida = next(e for e in entradas if e["estado"] == ESTADO_ENTRADA_COMPRADA)
    else:
        id_entrada = _entero(id_entrada, "id_entrada")
        elegida = next((e for e in entradas if e["id_entrada"] == id_entrada), None)
        if not elegida:
            raise ValueError("La entrada indicada no pertenece a esta compra.")
        if elegida["estado"] == ESTADO_ENTRADA_CANCELADA:
            raise ValueError("La entrada indicada está cancelada.")

    if not compras_repository.canjear_entrada(id_compra, elegida["id_entrada"]):
        raise ValueError("Esa entrada ya fue canjeada previamente.")
    return 1


def _entero(valor, campo: str) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"El campo '{campo}' debe ser un número entero.")


def _validar_una_unidad(id_compra: int, servicios: list[dict], categoria: str, cancelada: bool, id_detalle) -> int:
    nombre = NOMBRES_CATEGORIA[categoria]
    resumen = _resumen_servicios(servicios, categoria, cancelada)
    if resumen["total"] == 0:
        raise ValueError(f"La compra no incluye {nombre}.")
    if resumen["cancelada"]:
        raise ValueError("La compra está cancelada: sus servicios no son válidos.")
    if resumen["pendientes"] == 0:
        raise ValueError(MENSAJES_YA_CANJEADO[categoria])

    if id_detalle is None:
        elegido = next(i for i in resumen["items"] if i["pendientes"] > 0)
    else:
        id_detalle = _entero(id_detalle, "id_detalle")
        elegido = next((i for i in resumen["items"] if i["id_detalle"] == id_detalle), None)
        if not elegido:
            raise ValueError(f"El servicio indicado no pertenece a {nombre} de esta compra.")
        if elegido["pendientes"] == 0:
            raise ValueError("Esa unidad ya fue canjeada previamente.")

    if not compras_repository.canjear_unidad_servicio(id_compra, elegido["id_detalle"]):
        raise ValueError("Esa unidad ya fue canjeada previamente.")
    return 1


def validar_canje(codigo_qr: str, categoria: str, id_detalle=None, id_entrada=None) -> dict:
    categoria = (categoria or "").strip().lower()
    if categoria not in CATEGORIAS_VALIDACION:
        raise ValueError(
            "La categoría debe ser una de: " + ", ".join(CATEGORIAS_VALIDACION) + "."
        )

    primera, entradas, servicios = _cargar_compra(codigo_qr)
    id_compra = primera["id_compra"]

    estado_validacion, mensaje_validacion = _evaluar_ventana(primera.get("fecha_hora_proyeccion"))
    if estado_validacion != ESTADO_VALIDACION_VALIDA:
        raise ValueError(mensaje_validacion)

    if categoria == CATEGORIA_ENTRADAS:
        canjeados = _validar_una_entrada(id_compra, entradas, id_entrada)
    else:
        canjeados = _validar_una_unidad(
            id_compra, servicios, categoria, _compra_cancelada(entradas), id_detalle
        )

    # se vuelve a consultar para devolver el estado real posterior al canje
    resumen = consultar_compra(codigo_qr)
    resumen["categoria_validada"] = categoria
    resumen["unidades_canjeadas"] = canjeados
    # si se canjeó al menos una entrada y ya no quedan pendientes, se envía el correo de reseña
    if (
        categoria == CATEGORIA_ENTRADAS
        and canjeados > 0
        and resumen["categorias"][CATEGORIA_ENTRADAS]["pendientes"] == 0
    ):
        token_resena = URLSafeTimedSerializer(clave_secreta(), salt="resena-pelicula").dumps({
            "id_usuario": primera["id_usuario"],
            "id_pelicula": primera["id_pelicula"],
        })
        enviar_correo_resena(
            destinatario=primera["email_usuario"],
            nombre_usuario=primera["nombre_usuario"],
            pelicula=primera["pelicula"],
            token=token_resena,
        )

    return resumen
