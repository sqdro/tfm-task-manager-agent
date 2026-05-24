"""
Servicio para generar enlaces de eventos en Google Calendar
"""

from urllib.parse import urlencode
from datetime import datetime, timedelta


def generate_google_calendar_link(
    title: str,
    start_time: datetime,
    description: str = "",
    location: str = "",
    duration_minutes: int = 60,
    ) -> str:
    """Genera un enlace para crear un evento en Google Calendar"""

    # Calcular la hora de finalización sumando la duración al inicio
    end_time = start_time + timedelta(minutes=duration_minutes)

    # Construir los parámetros para el enlace de Google Calendar
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": (
            f"{start_time.strftime('%Y%m%dT%H%M%S')}/"
            f"{end_time.strftime('%Y%m%dT%H%M%S')}"
        ),
        "details": description or "",
        "location": location or "",
    }

    return ("https://calendar.google.com/calendar/render?" + urlencode(params))
