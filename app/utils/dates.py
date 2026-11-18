from datetime import datetime, timedelta, timezone

FORMATO_DATETIME = "%Y-%m-%d %H:%M:%S"
FORMATO_FECHA_HORA_LEGIBLE = "%d/%m/%Y %H:%M"

def ahora_argentina() -> datetime:
    """Hora actual de Argentina sin zona horaria, comparable con las fechas guardadas en la base."""
    return datetime.now(timezone(timedelta(hours=-3))).replace(tzinfo=None)

def string_a_datetime(fecha_str: str) -> datetime:
    """Convierte un string entrante a un objeto datetime."""
    return datetime.strptime(fecha_str, FORMATO_DATETIME)

def datetime_a_string(dt: datetime) -> str:
    """Formatea un objeto datetime a string estándar para SQL/JSON."""
    return dt.strftime(FORMATO_DATETIME)