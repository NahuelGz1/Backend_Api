from flask import Blueprint, jsonify, request

from db import obtener_conexion
servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios")
    filas = cursor.fetchall()
    cursor.close()
    conexion.close()

    servicios = []
    for fila in filas:
        servicios.append({
            "id": fila[0],
            "nombre": fila[1],
            "descripcion": fila[2],
            "precio": float(fila[3])
        })


    return jsonify(servicios), 200


@servicios_bp.route("/servicios", methods=["POST"])
def crear_servicio():
    data = request.get_json()

    if not data or "nombre" not in data or "precio" not in data:
        return jsonify({"error": "Faltan datos: nombre y precio son obligatorios"}), 400

    nombre = data["nombre"]
    descripcion = data.get("descripcion")
    precio = data["precio"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO servicios (nombre, descripcion, precio) VALUES (%s, %s, %s)",
        (nombre, descripcion, precio)
    )
    conexion.commit()
    nuevo_id = cursor.lastrowid
    cursor.close()
    conexion.close()

    return jsonify({"id": nuevo_id, "nombre": nombre, "descripcion": descripcion, "precio": float(precio)}), 201


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PUT"])
def modificar_servicio(servicio_id: int):
    datos = request.get_json()

    if "nombre" not in datos or "precio" not in datos:
        return jsonify({"error": "Faltan datos: nombre y precio"}), 400

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM servicios WHERE id = %s", (servicio_id,))
    fila = cursor.fetchone()
    if fila is None:
        cursor.close()
        conexion.close()
        return jsonify({"error": "Servicio no encontrado"}), 404

    cursor.execute(
        "UPDATE servicios SET nombre = %s, descripcion = %s, precio = %s WHERE id = %s",
        (datos["nombre"], datos.get("descripcion"), datos["precio"], servicio_id)
    )
    conexion.commit()
    cursor.close()
    conexion.close()

    
    return jsonify({"mensaje": "Servicio modificado"}), 200


@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
def desactivar_servicio(servicio_id: int):

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM servicios WHERE id = %s", (servicio_id,))
    fila = cursor.fetchone()
    if fila is None:
        cursor.close()
        conexion.close()
        return jsonify({"error": "Servicio no encontrado"}), 404

    cursor.execute("DELETE FROM servicios WHERE id = %s", (servicio_id,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return jsonify({"mensaje": "Servicio eliminado"}), 200

    




