from app.db import obtener_conexion, ejecutar_consulta, ejecutar_mutacion
from .response import responder_exito, responder_error
from .security import hashear_contraseña, verificar_contraseña, generar_token_acceso
from .decorators import requiere_autenticacion, requiere_administrador
from .dates import string_a_datetime, datetime_a_string
from .qr import generar_codigo_qr
from .tmdb import consultar_catalogo_tmdb