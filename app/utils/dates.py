from datetime import datetime

FORMATO_DATETIME = "%Y-%m-%d %H:%M:%S"

def string_a_datetime(fecha_str: str) -> datetime:
    """Convierte un string entrante a un objeto datetime."""
    return datetime.strptime(fecha_str, FORMATO_DATETIME)

def datetime_a_string(dt: datetime) -> str:
    """Formatea un objeto datetime a string estándar para SQL/JSON."""
    return dt.strftime(FORMATO_DATETIME)