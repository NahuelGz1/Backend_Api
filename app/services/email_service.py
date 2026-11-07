import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

# Cargamos las variables del .env
load_dotenv()


def mock_url_for(endpoint: str, **kwargs) -> str:
    # Traduce las rutas de Flask a URLs del frontend para que los botones de los correos funcionen
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

    rutas = {
        "auth_views.iniciar_sesion": f"{frontend_url}/auth/iniciar-sesion",
        "auth_views.recuperar_contrasena": f"{frontend_url}/auth/recuperar-contrasena",
        "cliente_views.cartelera": f"{frontend_url}/cartelera",
    }

    return rutas.get(endpoint, f"{frontend_url}/{endpoint.replace('.', '/')}")


def _obtener_jinja_env() -> Environment:
    # Prepara el entorno de Jinja buscando las plantillas en la carpeta de templates del backend
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_templates = os.path.abspath(os.path.join(directorio_actual, "..", "templates", "emails"))

    env = Environment(loader=FileSystemLoader(ruta_templates))
    env.globals["url_for"] = mock_url_for
    return env


def renderizar_plantilla(nombre_plantilla: str, **contexto) -> str:
    # Busca la plantilla HTML, le pasa las variables y arma el HTML listo para mandar
    env = _obtener_jinja_env()
    plantilla = env.get_template(nombre_plantilla)
    return plantilla.render(**contexto)


def enviar_correo(destinatario: str, asunto: str, cuerpo: str, es_html: bool = False) -> bool:
    # Se conecta al servidor SMTP y envia el correo (texto o html)
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("[EMAIL ERROR] Faltan credenciales en el entorno.")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = asunto

    tipo_contenido = "html" if es_html else "plain"
    msg.attach(MIMEText(cuerpo, tipo_contenido, "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, destinatario, msg.as_string())

        print(f"[EMAIL SUCCESS] Correo enviado a: {destinatario}")
        return True

    except Exception as e:
        print(f"[EMAIL ERROR] Falló el envío: {e}")
        return False


def enviar_correo_cuenta_creada(destinatario: str, nombre_usuario: str) -> bool:
    # Arma el correo de bienvenida usando la plantilla HTML y lo manda
    asunto = "¡Bienvenido a Cine Paradiso - Cuenta creada con éxito!"

    cuerpo_html = renderizar_plantilla(
        "correo-cuenta-creada.html",
        nombre=nombre_usuario,
        email=destinatario
    )

    return enviar_correo(destinatario, asunto, cuerpo_html, es_html=True)
