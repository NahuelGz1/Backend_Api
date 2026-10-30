import io
import base64
import qrcode

def generar_codigo_qr(contenido: str) -> str:
    """Genera una imagen QR en formato base64 a partir de un texto o JSON."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(contenido)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')