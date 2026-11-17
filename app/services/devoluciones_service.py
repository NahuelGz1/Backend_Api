from flask import current_app

from app.repositories import compras_repository, funciones_repository
from app.services import funciones_service
from app.services.email_service import enviar_correo_cancelacion_funcion
from app.services.reserva_service import texto_butacas

LARGO_MAXIMO_MOTIVO = 255


def _validar_motivo(datos: dict) -> str:
    motivo = datos.get("motivo")
    if not isinstance(motivo, str) or not motivo.strip():
        raise ValueError("Tenés que indicar el motivo de la cancelación, se les envía a los compradores", 400)
    motivo = " ".join(motivo.split())
    if len(motivo) > LARGO_MAXIMO_MOTIVO:
        raise ValueError(f"El motivo no puede tener más de {LARGO_MAXIMO_MOTIVO} caracteres", 400)
    return motivo


def _agrupar_por_compra(entradas: list[dict]) -> list[dict]:
    compras = {}
    for entrada in entradas:
        compra = compras.setdefault(entrada["id_compra"], {
            "id_compra": entrada["id_compra"],
            "codigo_qr": entrada["codigo_qr"],
            "nombre": entrada["nombre"],
            "email": entrada["email"],
            "butacas": [],
            "precio_entrada": float(entrada["precio_historico"]),
            "subtotal_entradas": 0.0,
        })
        compra["butacas"].append(int(entrada["numero_butaca"]))
        compra["subtotal_entradas"] += float(entrada["precio_historico"])
    return list(compras.values())


def _fecha_legible(fecha) -> str:
    try:
        return fecha.strftime("%d/%m/%Y · %H:%M")
    except AttributeError:
        return str(fecha)


def _avisar_por_mail(funcion: dict, compra: dict, servicios: list[dict], motivo: str) -> bool:
    detalles = {
        "nombre": compra["nombre"] or "Cliente",
        "email": compra["email"],
        "codigo_operacion": f"CP-{compra['id_compra']}",
        "codigo_qr": compra["codigo_qr"],
        "motivo": motivo,
        "pelicula_titulo": funcion["pelicula_titulo"],
        "pelicula_poster": funcion.get("pelicula_poster") or "",
        "funcion_fecha_hora": _fecha_legible(funcion["fecha_hora_proyeccion"]),
        "complejo_sala": f"{funcion['sala_local']} · {funcion['sala_nombre']}",
        "butacas_resumen": texto_butacas(compra["butacas"]),
        "cantidad_entradas": len(compra["butacas"]),
        "precio_entrada": compra["precio_entrada"],
        "subtotal_entradas": compra["subtotal_entradas"],
        "servicios": servicios,
        "subtotal_servicios": compra["subtotal_servicios"],
        "total_devolucion": compra["total_devolucion"],
    }
    try:
        return enviar_correo_cancelacion_funcion(compra["email"], detalles)
    except Exception as error:
        current_app.logger.error("No se pudo enviar el aviso de cancelación de la compra %s: %s", compra["id_compra"], error)
        return False


def cancelar_funcion(funcion_id: int, datos: dict) -> dict:
    funcion = funciones_service.verificar_funcion_cancelable(funcion_id)
    motivo = _validar_motivo(datos)

    # se cancelan las entradas vendidas, asi el QR de cada compra deja de servir
    entradas = funciones_repository.cancelar_funcion(funcion_id, motivo)
    compras = _agrupar_por_compra(entradas)

    total_devuelto = 0.0
    correos_enviados = 0
    for compra in compras:
        servicios = compras_repository.obtener_servicios_por_compra(compra["id_compra"])
        for servicio in servicios:
            servicio["subtotal"] = float(servicio["precio"]) * int(servicio["cantidad"])
        compra["subtotal_servicios"] = sum(s["subtotal"] for s in servicios)
        compra["total_devolucion"] = compra["subtotal_entradas"] + compra["subtotal_servicios"]
        total_devuelto += compra["total_devolucion"]

        if compra["email"] and _avisar_por_mail(funcion, compra, servicios, motivo):
            correos_enviados += 1

    return {
        "funcion": funciones_service.obtener_funcion_por_id(funcion_id, es_admin=True),
        "motivo": motivo,
        "compras_afectadas": len(compras),
        "entradas_canceladas": len(entradas),
        "total_devuelto": total_devuelto,
        "correos_enviados": correos_enviados,
    }
