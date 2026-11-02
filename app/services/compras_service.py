from datetime import datetime
from app.repositories.compras_repository import (crear_entrada, obtener_entradas_por_id,
    obtener_entradas_por_usuario, cancelar_entrada, crear_compra_servicio,
    obtener_compras_servicios_por_usuario, cancelar_compra_servicio, verificar_butaca_ocupada)
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

def obtener_entradas_usuario(id_usuario):

    entradas = obtener_entradas_por_usuario(id_usuario)
    servicios = obtener_compras_servicios_por_usuario(id_usuario)

    if not entradas and not servicios:
        return {"mensaje": "No se encontraron compras para este usuario."}, 404

    return {
        "entradas": entradas,
        "servicios": servicios}, 200 