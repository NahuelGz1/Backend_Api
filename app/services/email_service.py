import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Aseguramos la carga de variables de entorno
load_dotenv()

def enviar_correo(destinatario: str, asunto: str, cuerpo_texto: str) -> bool:
    """
    Envia un correo utilizando el servidor SMTP configurado en el archivo .env.
    """
    # Configuracion del servidor SMTP
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    # Si no se encuentran las credenciales, avisa por consola y frena para que no se rompa
    if not sender_email or not sender_password:
        print("[EMAIL ERROR] No se encontraron las credenciales de correo en entorno.")
        return False

    #Creación del mensaje
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))

    try:
        # Abrimos una conexión con el servidor de Google usando el puerto 587 y encriptación TLS.
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, destinatario, msg.as_string())
        print(f"[EMAIL SUCCESS] Correo enviado exitosamente a: {destinatario}")
        return True
    
    except Exception as e:

        print(f"[EMAIL ERROR] Ocurrió un error al enviar el correo: {e}")
        return False
