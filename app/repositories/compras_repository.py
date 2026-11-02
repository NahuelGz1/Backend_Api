from app.db import ejecutar_consulta, ejecutar_mutacion
#PARTE DE ENTRADAS
#crear entrada (POST)
def crear_entrada(id_usuario, id_funcion, numero_butaca, codigo_qr):

    sql = """
        INSERT INTO entradas
        (id_usuario, id_funcion, numero_butaca, codigo_qr)
        VALUES (%s, %s, %s, %s)
        """
    parametros = (id_usuario, id_funcion, numero_butaca, codigo_qr)
    return ejecutar_mutacion(sql, parametros)

#obtener la entrada por id (GET)
def obtener_entradas_por_id(entrada_id):
    sql = """
        SELECT * FROM entradas
        WHERE id = %s """
    parametros = (entrada_id,)
    return ejecutar_consulta(sql, parametros)

#Obtener todas las entradas de un usuario
def obtener_entradas_por_usuario(id_usuario):
    sql = """
        SELECT * FROM entradas
        WHERE id_usuario = %s
        """
    parametros = (id_usuario,)
    return ejecutar_consulta(sql, parametros)

#cambiar el estado de la entrada a cancelado (PUT)
def cancelar_entrada(entrada_id):
    sql = """
        UPDATE entradas
        SET estado = 'cancelada'
        WHERE id = %s"""
    parametros = (entrada_id,)
    return ejecutar_mutacion(sql, parametros)

#PARTE DE SERVICIOS
#comprar servicio (POST)
def crear_compra_servicio(id_usuario, id_servicio, fecha_hora_compra):
    sql = """
        INSERT INTO compras_servicios
        (id_usuario, id_servicio, fecha_hora_compra)
        VALUES (%s, %s, %s)"""
    parametros = (id_usuario, id_servicio, fecha_hora_compra)
    return ejecutar_mutacion(sql, parametros)

#obtener todas las compras de servicios de un usuario (GET)
def obtener_compras_servicios_por_usuario(id_usuario):
    sql = """SELECT * FROM compras_servicios
             WHERE id_usuario = %s"""
    parametros = (id_usuario,)
    return ejecutar_consulta(sql, parametros)

#cambiar el estado de la compra a cancelada (PUT)
def cancelar_compra_servicio(compra_id):
    sql = """
        UPDATE compras_servicios
        SET estado = 'cancelado'
        WHERE id = %s"""
    parametros = (compra_id,)   
    return ejecutar_mutacion(sql, parametros)

#verificar si la butaca ya está ocupada para una función específica
def verificar_butaca_ocupada(id_funcion, numero_butaca):
    sql = """
        SELECT * FROM entradas
        WHERE id_funcion = %s AND numero_butaca = %s AND estado != 'cancelada'
    """
    parametros = (id_funcion, numero_butaca)
    resultado = ejecutar_consulta(sql, parametros)
    return len(resultado) > 0