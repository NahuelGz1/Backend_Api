# precios
PRECIO_ENTRADA_FIJO = 10000.00
MONEDA_SIMBOLO = "$"

# roles de usuario
ROL_ADMINISTRADOR = "administrador"
ROL_CLIENTE = "cliente"

# estados de entradas
ESTADO_ENTRADA_COMPRADA = "comprada"
ESTADO_ENTRADA_UTILIZADA = "utilizada"
ESTADO_ENTRADA_CANCELADA = "cancelada"

# estados de funciones (se calculan con la fecha, la ocupacion y las marcas activo/eliminada)
ESTADO_FUNCION_EN_VENTA = "en_venta"
ESTADO_FUNCION_AGOTADA = "agotada"
ESTADO_FUNCION_VENTA_CERRADA = "venta_cerrada"
ESTADO_FUNCION_FINALIZADA = "finalizada"
ESTADO_FUNCION_ELIMINADA = "eliminada"

# largo del hash qr
LARGO_HASH_QR = 30

# categorías de validación de QR
CATEGORIA_ENTRADAS = "entradas"
CATEGORIA_VIP = "vip"
CATEGORIA_SERVICIOS = "servicios"
CATEGORIA_ESTACIONAMIENTO = "estacionamiento"
CATEGORIAS_VALIDACION = (
    CATEGORIA_ENTRADAS,
    CATEGORIA_VIP,
    CATEGORIA_SERVICIOS,
    CATEGORIA_ESTACIONAMIENTO,
)