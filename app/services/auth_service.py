from app.repositories.auth_repository import (
    buscar_por_email,
    crear_usuario,
    obtener_historial_entradas_por_usuario,
    obtener_historial_servicios_por_usuario,
    obtener_usuario_por_id,
)
from app.utils.dates import datetime_a_string
from app.utils.security import (
    generar_token_acceso,
    hashear_contraseña,
    verificar_contraseña,
)
from datetime import datetime

def registrar_usuario(nombre: str, email: str, password: str, rol: str = "cliente") -> dict:
    """
    Registra un nuevo usuario cifrando su contraseña.
    Lanza ValueError si el email ya existe.
    """
    if buscar_por_email(email):
        raise ValueError("El correo electrónico ya se encuentra registrado.")

    password_hash = hashear_contraseña(password)
    resultado = crear_usuario(nombre=nombre, email=email, password_hash=password_hash, rol=rol)

    if isinstance(resultado, dict) and "error" in resultado:
        raise ValueError(resultado["error"])

    return resultado


def autenticar_usuario(email: str, password: str) -> dict:
    """
    Valida las credenciales del usuario y genera un token JWT de sesión.
    Lanza ValueError(msg, 401) si las credenciales son inválidas.
    """
    usuario = buscar_por_email(email)

    if not usuario or not verificar_contraseña(password, usuario.get("password_hash", "")):
        raise ValueError("Credenciales inválidas", 401)

    rol_usuario = usuario.get("rol", "cliente")
    token = generar_token_acceso(usuario["id"], rol_usuario)

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": rol_usuario,
        },
    }


def consultar_perfil_usuario(id_usuario: int) -> dict:
    """
    Retorna la información del usuario autenticado.
    """
    usuario = obtener_usuario_por_id(id_usuario)
    if not usuario:
        raise ValueError("Usuario no encontrado", 404)
    return usuario


def consultar_historial_completo_usuario(id_usuario: int) -> dict:
    """
    Retorna el historial unificado de entradas y servicios del usuario.
    """
    entradas_bd = obtener_historial_entradas_por_usuario(id_usuario)
    servicios_bd = obtener_historial_servicios_por_usuario(id_usuario)

    lista_entradas = [
        {
            "id_entrada": fila["id_entrada"],
            "numero_butaca": fila["numero_butaca"],
            "codigo_qr": fila["codigo_qr"],
            "estado": fila["estado"],
            "funcion": {
                "id": fila["id_funcion"],
                "fecha_hora_proyeccion": datetime_a_string(fila["fecha_hora_proyeccion"]),
                "sala": fila["sala_nombre"],
                "local": fila["cine_local"],
            },
            "pelicula": {
                "titulo": fila["pelicula_titulo"],
                "poster": fila["pelicula_poster"],
                "duracion": fila["pelicula_duracion"],
            },
        }
        for fila in entradas_bd
    ]

    lista_servicios = [
        {
            "id_compra_servicio": fila["id_compra_servicio"],
            "id_servicio": fila["id_servicio"],
            "servicio": fila["servicio_nombre"],
            "precio": float(fila["precio"]) if fila["precio"] is not None else 0.0,
            "fecha_hora_compra": datetime_a_string(fila["fecha_hora_compra"]),
        }
        for fila in servicios_bd
    ]

    return {
        "entradas": lista_entradas,
        "servicios": lista_servicios,
    }

def consultar_perfil_completo_usuario(id_usuario: int) -> dict:
    """
    Retorna los datos del perfil formateados específicamente para el frontend (mi_perfil.html).
    """
    entradas_bd = obtener_historial_entradas_por_usuario(id_usuario)
    servicios_bd = obtener_historial_servicios_por_usuario(id_usuario)

    entradas_proximas = []
    peliculas_vistas = []
    ahora = datetime.now()

    for fila in entradas_bd:
        fecha_obj = fila["fecha_hora_proyeccion"]

        item = {
            "pelicula": {
                "titulo": fila["pelicula_titulo"],
                "poster_url": fila["pelicula_poster"],
            },
            "fecha": fecha_obj.strftime("%Y-%m-%d") if isinstance(fecha_obj, datetime) else str(fecha_obj).split(" ")[0],
            "horario": fecha_obj.strftime("%H:%M") if isinstance(fecha_obj, datetime) else str(fecha_obj).split(" ")[1][:5],
            "complejo": fila["cine_local"],
            "sala": fila["sala_nombre"],
            "butacas": fila["numero_butaca"],
            "cantidad_entradas": 1,
            "subtotal_entradas": "-",
            "subtotal_servicios": "-",
            "total": "-",
            "codigo_operacion": fila["id_entrada"],
        }

        if isinstance(fecha_obj, datetime) and fecha_obj >= ahora and fila["estado"] != "usada":
            entradas_proximas.append(item)
        else:
            peliculas_vistas.append(item)

    consumos_candy = []
    total_candy = 0.0

    for fila in servicios_bd:
        precio = float(fila["precio"]) if fila["precio"] is not None else 0.0
        total_candy += precio
        
        fecha_compra = fila["fecha_hora_compra"]
        fecha_str = fecha_compra.strftime("%Y-%m-%d") if isinstance(fecha_compra, datetime) else str(fecha_compra).split(" ")[0]

        consumos_candy.append({
            "nombre": fila["servicio_nombre"],
            "cantidad": 1,
            "precio_unitario": f"{precio:,.0f}",
            "fecha": fecha_str,
            "codigo_pedido": fila["id_compra_servicio"],
        })

    return {
        "entradas_proximas": entradas_proximas,
        "peliculas_vistas": peliculas_vistas,
        "consumos_candy": consumos_candy,
        "consumos_candy_total": f"{total_candy:,.0f}",
    }