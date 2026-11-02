from app.db import ejecutar_consulta, ejecutar_mutacion

def validar_acceso(codigo_qr: str) -> dict:
    sql = "SELECT id, estado, id_funcion, numero_butaca FROM entradas WHERE codigo_qr = %s"
    resultado = ejecutar_consulta(sql, (codigo_qr,))

    if not resultado:
        raise ValueError("Código QR inválido o no encontrado.")

    entrada = resultado[0]

    if entrada["estado"] == "cancelada":
        raise ValueError("Acceso denegado: Esta entrada fue cancelada.")
    if entrada["estado"] == "utilizada":
        raise ValueError("Acceso denegado: Esta entrada ya fue escaneada anteriormente.")

    ejecutar_mutacion("UPDATE entradas SET estado = 'utilizada' WHERE id = %s", (entrada["id"],))

    return {
        "id_entrada": entrada["id"],
        "id_funcion": entrada["id_funcion"],
        "numero_butaca": entrada["numero_butaca"],
        "estado": "utilizada"
    }