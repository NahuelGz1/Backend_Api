import hashlib
import time
from flask import current_app
from app.repositories import auth_repository, compras_repository, funciones_repository
from app.services.email_service import enviar_correo_compra
from datetime import datetime, timedelta

from app.utils.qr import generar_codigo_qr
from app.utils.constantes import PRECIO_ENTRADA_FIJO, LARGO_HASH_QR, ESTADO_ENTRADA_CANCELADA

def procesar_compra(datos: dict, id_usuario: int) -> dict:
    id_funcion = datos.get("id_funcion")
    butacas = datos.get("butacas")
    servicios = datos.get("servicios", [])

    if not id_funcion or not butacas or not isinstance(butacas, list):
        raise ValueError("Faltan datos obligatorios: 'id_funcion' y 'butacas' (lista)")

    conflictos = []
    for butaca in butacas:
        if compras_repository.verificar_butaca_ocupada(id_funcion, butaca):
            conflictos.append(butaca)

    if conflictos:
        raise ValueError(f"Las butacas {conflictos} ya se encuentran ocupadas.")

    codigo_qr = hashlib.sha256(
        f"compra-{id_usuario}-{id_funcion}-{time.time()}".encode()
    ).hexdigest()[:LARGO_HASH_QR]
    entradas_data = []
    entradas_generadas_info = []

    for butaca in butacas:
        entradas_data.append({
            "id_funcion": id_funcion,
            "numero_butaca": butaca,
            "precio": PRECIO_ENTRADA_FIJO,
            "qr": codigo_qr
        })

        entradas_generadas_info.append({
            "numero_butaca": butaca,
            "codigo_qr_texto": codigo_qr,
            "qr_imagen_base64": generar_codigo_qr(codigo_qr) if butaca == butacas[0] else None
        })

    id_compra = compras_repository.guardar_compra_completa(
        id_usuario, codigo_qr, entradas_data, servicios
    )
    try:
        usuario = auth_repository.obtener_usuario_por_id(id_usuario)
        funcion_info = funciones_repository.buscar_funcion_por_id(id_funcion)
        if usuario and usuario.get("email"):
            detalles_email = {
                "nombre": usuario.get("nombre", "Cliente"),
                "email": usuario.get("email"),
                "codigo_operacion": f"CP-{id_compra}",
                "pelicula_titulo": funcion_info.get("pelicula_titulo") if funcion_info else "Película",
                "pelicula_poster": funcion_info.get("pelicula_poster") if funcion_info else "",
                "funcion_fecha_hora": str(funcion_info.get("fecha_hora_proyeccion")) if funcion_info else "",
                "complejo_sala": f"{funcion_info.get('sala_local', '')} · {funcion_info.get('sala_nombre', '')}" if funcion_info else "",
                "butacas_resumen": f"Butacas: {', '.join(str(b) for b in butacas)}",
                "entradas": entradas_generadas_info,
            }
            enviar_correo_compra(usuario["email"], detalles_email)
    except Exception as e:
        current_app.logger.error("Error al enviar correo de compra: %s", e)

    return {
        "id_compra": id_compra,
        "mensaje": "Compra procesada exitosamente",
        "codigo_qr_texto": codigo_qr,
        "qr_imagen_base64": generar_codigo_qr(codigo_qr),
        "entradas": entradas_generadas_info
    }

def obtener_detalle_compra(compra_id: int, id_usuario: int) -> dict:
    entrada = compras_repository.obtener_entrada_por_id(compra_id)

    if not entrada:
        raise ValueError(f"No se encontró la compra con ID {compra_id}")

    if entrada["id_usuario"] != id_usuario:
        raise PermissionError("No tienes permiso para ver el detalle de esta entrada.")

    del entrada["id_usuario"]
    entrada["fecha_hora_proyeccion"] = str(entrada["fecha_hora_proyeccion"])
    return entrada

def cancelar_compra(compra_id: int, id_usuario: int) -> dict:
    datos_compra = compras_repository.obtener_datos_resumen_compra(compra_id)

    if not datos_compra:
        raise ValueError("La compra solicitada no existe.")

    if datos_compra["id_usuario"] != id_usuario:
        raise PermissionError("No tienes permiso para cancelar esta compra.")

    #validación de la regla de las 2 horas
    fecha_proyeccion = datos_compra["fecha_proyeccion"]

    #casteo por si la base de datos devuelve un string en vez de objeto datetime
    if isinstance(fecha_proyeccion, str):
        fecha_proyeccion = datetime.strptime(fecha_proyeccion, "%Y-%m-%d %H:%M:%S")

    tiempo_restante = fecha_proyeccion - datetime.now()
    if tiempo_restante < timedelta(hours=2):
        raise ValueError("No se puede cancelar la compra. Faltan menos de 2 horas para la función.")

    # cancelación logica de las butacas (libera los lugares conservando el hiistorial)
    filas_afectadas = compras_repository.cancelar_entradas_por_compra(compra_id)
    if not filas_afectadas:
        raise ValueError("La compra ya se encuentra utilizada, previamente cancelada, o no es válida.")

    return {
        "id_compra": compra_id,
        "estado_actual": ESTADO_ENTRADA_CANCELADA,
        "mensaje": "Compra y servicios adicionales cancelados exitosamente."
    }