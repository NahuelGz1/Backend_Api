from datetime import datetime
from app.repositories.compras_repository import (crear_entrada, obtener_entradas_por_id,
    obtener_entradas_por_usuario, cancelar_entrada, crear_compra_servicio, 
    cancelar_compra_servicio, verificar_butaca_ocupada, obtener_compra_servicio_por_id)
from app.repositories.funciones_repository import obtener_funcion_por_id

def procesar_compra(datos_compra, id_usuario):
    #Verificar si la funcion existe y si la butaca está disponible
    id_funcion = datos_compra.get("id_funcion")
    lista_butaca = datos_compra.get("numero_butaca", [])
    lista_servicios = datos_compra.get("servicios", [])

    funcion = obtener_funcion_por_id(id_funcion)
    if not funcion:
        return {"error": "La función no existe."}
    
    for butacas in lista_butaca:
        if verificar_butaca_ocupada(id_funcion, butacas):
            return {"error": f"La butaca {butacas} ya está ocupada. Compra otra butaca."}
    
    for numero_butaca in lista_butaca:
        codigo_qr_temp = f"QR-{id_funcion}-{numero_butaca}-{id_usuario}"
        crear_entrada(id_usuario, id_funcion, numero_butaca)

    #Posibilidad de cambiar el date_time con un fecha_actual = datetime.now() por si datos_compra no tiene fecha_hora_compra, pero por ahora lo dejamos así
    date_time = datos_compra.get("fecha_hora_compra")
    if not date_time:
        date_time = datetime.now()
    for id_servicio in lista_servicios:
        crear_compra_servicio(id_usuario, id_servicio, date_time)

    return {"mensaje": "Compra procesada exitosamente."}

def obtener_detalle_compra_servicio(compra_id, id_usuario_peticion):
    # Recuerda que esta usa obtener_detalle_servicio_bd (la que tiene el JOIN)
    resultado = obtener_detalle_servicio_bd(compra_id)
    
    if not resultado:
        return {"error": "La compra de servicio no existe."}, 404
        
    compra = resultado[0] 
    
    if compra["id_usuario"] != id_usuario_peticion:
        return {"error": "No tienes permiso para ver esta compra de servicio."}, 403
        
    del compra["id_usuario"]
    
    return {"data": compra}, 200

def obtener_entradas_por_id(compra_id, id_usuario_peticion):

    resultado = obtener_entradas_por_id(compra_id)

    if not resultado:
        return {"error": "La compra no existe."}, 404

    compra = resultado[0]

    if compra["id_usuario"] != id_usuario_peticion:
        return {"error": "No tienes permiso para ver esta compra."}, 403

    return {"detalles": compra}, 200

def cancelar_entrada_usuario(entrada_id, id_usuario_peticion):

    resultado = obtener_entradas_por_id(entrada_id)

    if not resultado:
        return {"error": "La entrada no existe."}, 404

    entrada = resultado[0]

    if entrada["id_usuario"] != id_usuario_peticion:
        return {"error": "No tienes permiso para cancelar esta entrada."}, 403

    cancelar_entrada(entrada_id)
    return {"mensaje": "Entrada cancelada exitosamente."}, 200

def anular_compra_servicio(compra_id, id_usuario_peticion):

    resultado = obtener_compra_servicio_por_id(compra_id)

    if not resultado:
        return {"error": "La compra de servicio no existe."}, 404

    compra = resultado[0]

    if compra["id_usuario"] != id_usuario_peticion:
        return {"error": "No tienes permiso para cancelar esta compra de servicio."}, 403

    cancelar_compra_servicio(compra_id)
    return {"mensaje": "Compra de servicio cancelada exitosamente."}, 200
