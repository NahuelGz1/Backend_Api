import hashlib
import time
from app.repositories import compras_repository
from app.utils.qr import generar_codigo_qr

def procesar_compra(datos: dict, id_usuario: int) -> list:
    id_funcion = datos.get("id_funcion")
    butacas = datos.get("butacas")

    if not id_funcion or not butacas or not isinstance(butacas, list):
        raise ValueError("Faltan datos obligatorios: 'id_funcion' y 'butacas' (lista)")

    conflictos = []
    for butaca in butacas:
        if compras_repository.verificar_butaca_ocupada(id_funcion, butaca):
            conflictos.append(butaca)

    if conflictos:
        raise ValueError(f"Las butacas {conflictos} ya se encuentran ocupadas.")

    entradas_generadas = []
    for butaca in butacas:
        hash_qr = hashlib.sha256(f"{id_funcion}-{butaca}-{id_usuario}-{time.time()}".encode()).hexdigest()[:30]

        id_entrada = compras_repository.crear_entrada(id_usuario, id_funcion, butaca, hash_qr)
        imagen_base64 = generar_codigo_qr(hash_qr)

        entradas_generadas.append({
            "id_entrada": id_entrada,
            "numero_butaca": butaca,
            "codigo_qr_texto": hash_qr,
            "qr_imagen_base64": imagen_base64
        })

    return entradas_generadas

def obtener_detalle_compra(compra_id: int, id_usuario: int) -> dict:
    entrada = compras_repository.obtener_entrada_por_id(compra_id)

    if not entrada:
        raise ValueError(f"No se encontró la compra con ID {compra_id}")

    if entrada["id_usuario"] != id_usuario:
        raise PermissionError("No tienes permiso para ver el detalle de esta entrada.")

    del entrada["id_usuario"]
    entrada["fecha_hora_proyeccion"] = str(entrada["fecha_hora_proyeccion"])
    return entrada

def cancelar_entrada(entrada_id: int, id_usuario: int) -> dict:
    entrada = compras_repository.obtener_entrada_por_id(entrada_id)

    if not entrada:
        raise ValueError("La entrada no existe.")

    if entrada["id_usuario"] != id_usuario:
        raise PermissionError("No tienes permiso para cancelar esta entrada.")

    if entrada["estado"] != "comprada":
        raise ValueError("La entrada ya se encuentra utilizada o cancelada.")

    filas_afectadas = compras_repository.actualizar_estado_entrada(entrada_id, "cancelada")
    if not filas_afectadas:
        raise ValueError("Error al intentar cancelar la entrada.")

    return {"id_entrada": entrada_id, "estado_actual": "cancelada"}