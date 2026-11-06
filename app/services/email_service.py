import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode, urlsplit

from flask import current_app


def enviar_recuperacion(email, token):
    config = current_app.config
    base = config["PASSWORD_RESET_URL"]
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
        raise RuntimeError("PASSWORD_RESET_URL debe ser una URL absoluta sin query ni fragmento")
    mensaje = EmailMessage()
    mensaje["Subject"] = "Recuperar acceso a Cine Paradiso"
    mensaje["From"] = config["SMTP_FROM"]
    mensaje["To"] = email
    enlace = base + "?" + urlencode({"token": token})
    mensaje.set_content(
        f"Para crear una nueva contraseña, abrí este enlace:\n{enlace}\n\n"
        f"Vence en {config['PASSWORD_RESET_MAX_AGE'] // 60} minutos y queda invalidado al cambiar tu clave.\n"
        "Si no solicitaste el cambio, ignorá este correo."
    )
    try:
        with smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"], timeout=10) as smtp:
            if config["SMTP_STARTTLS"]:
                smtp.starttls(context=ssl.create_default_context())
            if config["SMTP_USERNAME"]:
                smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            rechazados = smtp.send_message(mensaje)
            if rechazados:
                raise smtplib.SMTPException("Entrega rechazada")
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.error("Falló la entrega del correo de recuperación")
        raise ValueError("No fue posible procesar la recuperación. Intentá más tarde", 503) from error