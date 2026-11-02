import hashlib
import time
from app.db import ejecutar_consulta, ejecutar_mutacion
from app.services import ocupacion_service
from app.utils.qr import generar_codigo_qr

def procesar_compra(datos: dict, id_usuario: int) -> list:
    id_funcion = datos.get("id_funcion")
    butacas = datos.get("butacas")

    if not id_funcion or not butacas or not isinstance(butacas, list):
        raise ValueError("Faltan datos obligatorios: 'id_funcion' y 'butacas' (lista)")

    disponibilidad = ocupacion_service.obtener_estado_butacas(id_funcion)
    ocupadas = [b["numero_butaca"] for b in disponibilidad if b["estado"] == "ocupada"]

    conflictos = [b for b in butacas if b in ocupadas]
    if conflictos:
        raise ValueError(f"Las butacas {conflictos} ya se encuentran ocupadas.")

    sql_entrada = """
                  INSERT INTO entradas (id_usuario, id_funcion, numero_butaca, codigo_qr, estado)
                  VALUES (%s, %s, %s, %s, 'comprada') \
                  """

    entradas_generadas = []
    for butaca in butacas:
        hash_qr = hashlib.sha256(f"{id_funcion}-{butaca}-{id_usuario}-{time.time()}".encode()).hexdigest()[:30]
        id_entrada = ejecutar_mutacion(sql_entrada, (id_usuario, id_funcion, butaca, hash_qr))
        imagen_base64 = generar_codigo_qr(hash_qr)

        entradas_generadas.append({
            "id_entrada": id_entrada,
            "numero_butaca": butaca,
            "codigo_qr_texto": hash_qr,
            "qr_imagen_base64": imagen_base64
        })

    return entradas_generadas


def obtener_detalle_compra(compra_id: int, id_usuario: int) -> dict:
    sql = """
          SELECT e.id AS id_entrada, e.id_usuario, e.numero_butaca, e.codigo_qr, e.estado,
                 f.fecha_hora_proyeccion, p.titulo AS pelicula, s.nombre AS sala, s.local
          FROM entradas e
                   JOIN funciones f ON e.id_funcion = f.id
                   JOIN peliculas p ON f.id_pelicula = p.id
                   JOIN salas s ON f.id_sala = s.id
          WHERE e.id = %s \
          """
    resultado = ejecutar_consulta(sql, (compra_id,))

    if not resultado:
        raise ValueError(f"No se encontró la compra con ID {compra_id}")

    entrada = resultado[0]

    # valida propiedad
    if entrada["id_usuario"] != id_usuario:
        raise PermissionError("No tienes permiso para ver el detalle de esta entrada.")

    # limpia campo privado id_usuario antes de devolverlo
    del entrada["id_usuario"]
    entrada["fecha_hora_proyeccion"] = str(entrada["fecha_hora_proyeccion"])
    return entrada


def cancelar_entrada(entrada_id: int) -> dict:
    sql = "UPDATE entradas SET estado = 'cancelada' WHERE id = %s AND estado = 'comprada'"
    filas_afectadas = ejecutar_mutacion(sql, (entrada_id,))

    if not filas_afectadas:
        raise ValueError("Entrada no encontrada o ya se encuentra utilizada/cancelada.")

    return {"id_entrada": entrada_id, "estado_actual": "cancelada"}