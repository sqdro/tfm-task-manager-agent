"""
Servicio de gestión de eventos de calendario
"""

from datetime import datetime
from typing import List, Optional

from app.persistence.database import events_collection
from app.services.calendar_service import generate_google_calendar_link
from app.services.llm_service import get_embedding
from app.utils.logger import get_logger


logger = get_logger(__name__)

DATE_FORMATS = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"]


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parsea una cadena de fecha/hora en un objeto datetime"""

    if not datetime_str or not datetime_str.strip():
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(datetime_str.strip(), fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(datetime_str.strip())
    except ValueError:
        logger.warning(f"Formato de fecha/hora no reconocido: {datetime_str}")

    return None


def create_event(
    title: str,
    datetime_str: str,
    description: Optional[str] = None,
    location: Optional[str] = None
    ) -> str:
    """Crea un nuevo evento en la base de datos y genera un enlace de calendario"""


    if not title or not title.strip():
        logger.warning("Intento de crear evento con título vacío")
        return "El título del evento no puede estar vacío."

    start_time = parse_datetime(datetime_str)
    if not start_time:
        return "La fecha/hora del evento debe tener formato válido (YYYY-MM-DD o YYYY-MM-DD HH:MM)."

    if events_collection.find_one({"title": title, "start_time": start_time}):
        logger.info(f"Evento '{title}' ya existe en esa fecha")
        return f"El evento '{title}' ya está registrado para esa fecha."

    event = {
        "title": title,
        "embedding": get_embedding(title),
        "start_time": start_time,
        "description": description,
        "location": location,
        "status": "scheduled",
        "created_at": datetime.now()
    }

    try:
        # Insertar evento en la base de datos
        result = events_collection.insert_one(event)

        # Generar enlace de calendario para el evento creado
        calendar_link = generate_google_calendar_link(
            title,
            start_time,
            description or "",
            location or "",
        )

        logger.info(f"Evento '{title}' creado correctamente (ID: {result.inserted_id})")

        return (
            f"Evento '{title}' programado para {start_time.strftime('%Y-%m-%d %H:%M')} correctamente.\n"
            f"[Añadir a Google Calendar]({calendar_link})"
        )
    except Exception as e:
        logger.error(f"Error creando evento '{title}': {e}")
        return f"Error al crear evento: {str(e)}"


def list_events(before_date: Optional[str] = None) -> List[str]:
    """Lista eventos de la base de datos, opcionalmente filtrando por fecha"""

    query = {}

    # Filtrar por fecha si se proporciona
    if before_date:
        parsed_before = parse_datetime(before_date)
        if not parsed_before:
            return ["El filtro before_date debe ser válido (YYYY-MM-DD o YYYY-MM-DD HH:MM)."]
        query["start_time"] = {"$lt": parsed_before}

    try:
        events = list(events_collection.find(query))
        events.sort(key=lambda event: event["start_time"])
        if not events:
            return ["No hay eventos programados."]

        # Formatear evento
        formatted = []
        for event in events:
            start_time = event["start_time"].strftime("%Y-%m-%d %H:%M")
            description = event.get("description") or "Sin descripción"
            location = event.get("location") or "Sin ubicación"
            formatted.append(
                f"{event['title']} — {start_time} — {description} — {location}"
            )

        logger.info(f"Listando {len(events)} eventos")

        return formatted
    
    except Exception as e:
        logger.error(f"Error listando eventos: {e}")
        return [f"Error al listar eventos: {str(e)}"]


def update_event(
    title: str,
    datetime_str: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
    ) -> str:
    """Actualiza un evento existente y regenera el enlace de calendario"""

    if not title or not title.strip():
        return "El título del evento es obligatorio para actualizarlo."
    
    update_fields = {}

    # Recuperar evento existente para poder generar el enlace actualizado
    existing_event = events_collection.find_one({"title": title})
    if not existing_event:
        return f"No se encontró el evento '{title}'."

    # Validar y preparar campos de actualización
    if datetime_str:
        parsed_time = parse_datetime(datetime_str)
        if not parsed_time:
            return "La fecha/hora debe tener un formato válido."
        update_fields["start_time"] = parsed_time
    if description is not None:
        update_fields["description"] = description
    if location is not None:
        update_fields["location"] = location
    if not update_fields:
        return "No se especificaron cambios para el evento."

    try:
        # Actualizar evento en la base de datos
        result = events_collection.update_one(
            {"title": title},
            {"$set": update_fields},
        )

        if result.matched_count == 0:
            return f"No se encontró el evento '{title}'."

        # Construir valores finales tras la actualización
        new_start = update_fields.get("start_time", existing_event.get("start_time"))
        new_description = update_fields.get("description", existing_event.get("description") or "")
        new_location = update_fields.get("location", existing_event.get("location") or "")

        try:
            # Generar nuevo enlace de calendario con los datos actualizados
            calendar_link = generate_google_calendar_link(
                title,
                new_start,
                new_description,
                new_location,
            )

            logger.info(f"Evento '{title}' actualizado correctamente")

            return (
                f"Evento '{title}' actualizado correctamente.\n"
                f"[Abrir en Google Calendar]({calendar_link})"
            )
        except Exception:
            logger.info(f"Evento '{title}' actualizado, pero no se pudo generar enlace de calendario")
            return f"Evento '{title}' actualizado correctamente."
        
    except Exception as e:
        logger.error(f"Error actualizando evento '{title}': {e}")
        return f"Error al actualizar evento: {str(e)}"


def delete_event(title: str) -> str:
    """Elimina un evento existente"""

    if not title or not title.strip():
        return "El título del evento es obligatorio para eliminarlo."

    try:
        # Eliminar evento de la base de datos
        result = events_collection.delete_one({"title": title})

        if result.deleted_count == 0:
            return f"No se encontró el evento '{title}'."
        
        logger.info(f"Evento '{title}' eliminado correctamente")

        return f"Evento '{title}' eliminado correctamente."
    
    except Exception as e:
        logger.error(f"Error eliminando evento '{title}': {e}")
        return f"Error al eliminar evento: {str(e)}"


def execute_event_actions(actions: list) -> list:
    """Ejecuta una lista de acciones relacionadas con eventos de calendario"""
    
    results = []
    for action in actions:
        order = action.get("order")
        title = action.get("title")
        datetime_str = action.get("datetime")
        description = action.get("description")
        location = action.get("location")

        if order == "create_event":
            results.append(create_event(title, datetime_str, description, location))
        elif order == "list_events":
            results.extend(list_events(action.get("before_date")))
        elif order == "update_event":
            results.append(update_event(title, datetime_str, description, location))
        elif order == "delete_event":
            results.append(delete_event(title))
        else:
            results.append(f"Acción de evento desconocida: {order}")
    return results
