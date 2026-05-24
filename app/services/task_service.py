"""
Servicio de gestión de tareas
"""

from typing import List, Optional
from datetime import datetime
from app.persistence.database import tasks_collection, projects_collection
from app.services.llm_service import get_embedding
from app.utils.logger import get_logger
from app.services.project_service import create_project


logger = get_logger(__name__)


DEFAULT_PROJECT = "Default Project" # Proyecto por defecto para tareas sin proyecto especificado
DATE_FORMATS = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"]


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Intenta parsear una cadena de fecha/hora en varios formatos comunes"""

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


def create_task(
    task: str, 
    project: str, 
    priority: str = None, 
    due_date: Optional[datetime] = None
    ) -> str:
    """Crea una nueva tarea en un proyecto específico. Si el proyecto no existe, lo crea automáticamente"""

    if not task or not task.strip():
        logger.warning("Intento de crear tarea con título vacío")
        return "El título de la tarea no puede estar vacío."
    
    # Si el proyecto es None o vacío, usar proyecto por defecto
    if not project:
        logger.info(f"Proyecto no especificado, usando proyecto por defecto: '{DEFAULT_PROJECT}'")
        project = DEFAULT_PROJECT
        
        # Si el proyecto por defecto no existe, crearlo
        if not projects_collection.find_one({"name": project}):
            result = create_project(project)
            if "creado correctamente" not in result:
                logger.error(f"Error creando proyecto por defecto: {result}")
                return f"Error creando proyecto por defecto: {result}"
    else:
        # Verificar si el proyecto existe, si no lo crea
        if not projects_collection.find_one({"name": project}):
            logger.info(f"Proyecto '{project}' no encontrado, creando automáticamente.")
            result = create_project(project)
            if "creado correctamente" not in result:
                logger.error(f"Error creando proyecto '{project}': {result}")
                return f"Error creando proyecto '{project}': {result}"
    
    # Verificar si la tarea ya existe
    if tasks_collection.find_one({"task": task, "project": project}):
        logger.info(f"Tarea '{task}' ya existe en '{project}'")
        return f"La tarea '{task}' ya existe en '{project}'."
    
    try:
        # Crear e insertar tarea
        task_data = {
            "task": task,
            "embedding": get_embedding(task),
            "project": project,
            "priority": priority,
            "due_date": due_date,
            "created_at": datetime.now(),
            "completed": False
        }
        result = tasks_collection.insert_one(task_data)
        logger.info(f"Tarea '{task}' añadida al proyecto '{project}' (ID: {result.inserted_id})")
        return f"Tarea '{task}' añadida al proyecto '{project}'."
    
    except Exception as e:
        logger.error(f"Error añadiendo tarea '{task}': {e}")
        return f"Error al añadir tarea: {str(e)}"


def close_task(task: str, project: str) -> str:
    """Marca una tarea como completada"""

    # Si el proyecto es None o vacío, usar proyecto por defecto
    if not project:
        logger.info(f"Proyecto no especificado, usando proyecto por defecto: '{DEFAULT_PROJECT}'")
        project = DEFAULT_PROJECT

    # Verificar si el proyecto existe
    if not projects_collection.find_one({"name": project}):
        if project == DEFAULT_PROJECT:
            logger.warning("Proyecto no especificado")
            return "No se especificó un proyecto."
        logger.warning(f"Proyecto '{project}' no encontrado")
        return f"No existe el proyecto '{project}'."

    try:
        result = tasks_collection.update_one(
            {"task": task, "project": project},
            {"$set": {"completed": True}}
        )

        # Verificar si se actualizó alguna tarea
        if result.matched_count == 0:
            logger.warning(f"Tarea '{task}' no encontrada")
            return f"No se encontró la tarea '{task}' en el proyecto '{project}'."
        
        logger.info(f"Tarea '{task}' marcada como completada")
        return f"Tarea '{task}' marcada como completada."
    
    except Exception as e:
        logger.error(f"Error marcando tarea como completada: {e}")
        return f"Error: {str(e)}"


def list_tasks(
    project: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    completed: Optional[bool] = None,
    ) -> List[str]:
    """Lista las tareas de un proyecto, con opciones de filtrado por prioridad, fecha de vencimiento y estado de completado"""

    try:
        query = {}
        if project:
            if not projects_collection.find_one({"name": project}):
                logger.warning(f"Proyecto '{project}' no encontrado")
                return [f"No existe el proyecto '{project}'."]
            query["project"] = project
        else:
            logger.info("Proyecto no especificado, listando todas las tareas")

        if priority is not None:
            if priority not in ["high", "medium", "low"]:
                return [
                    f"Prioridad inválida: {priority}. Usa high, medium o low."
                ]
            query["priority"] = priority

        if completed is not None:
            query["completed"] = completed

        tasks = list(tasks_collection.find(query))

        if due_date is not None:
            parsed_due_date = parse_datetime(due_date)
            if not parsed_due_date:
                return [
                    "El filtro de fecha debe ser válido (YYYY-MM-DD o YYYY-MM-DD HH:MM)."
                ]

            def due_date_before(task):
                task_due = task.get("due_date")
                if task_due is None:
                    return False
                if isinstance(task_due, str):
                    parsed_task_due = parse_datetime(task_due)
                    return parsed_task_due is not None and parsed_task_due < parsed_due_date
                if isinstance(task_due, datetime):
                    return task_due < parsed_due_date
                return False

            tasks = [task for task in tasks if due_date_before(task)]

        if not tasks:
            if project:
                return [f"No hay tareas en '{project}' que coincidan con los criterios."]
            return ["No hay tareas que coincidan con los criterios."]

        priority_order = {
            "high": 1,
            "medium": 2,
            "low": 3,
        }
        tasks.sort(key=lambda x: priority_order.get(x.get("priority"), 99))

        task_list = []
        for t in tasks:
            creation_date = t["created_at"].strftime('%d/%m/%Y %H:%M')
            due_date_value = t.get("due_date")
            if due_date_value:
                if isinstance(due_date_value, str):
                    due_date_str = due_date_value
                elif isinstance(due_date_value, datetime):
                    due_date_str = due_date_value.strftime('%d/%m/%Y %H:%M')
                else:
                    due_date_str = "Sin fecha límite"
            else:
                due_date_str = "Sin fecha límite"
            project_name = t.get("project", "Sin proyecto")
            completed_str = "yes" if t.get("completed") else "no"
            task_list.append(
                f"[{project_name}] {t['task']} — Prioridad: {t['priority']} — Completada: {completed_str} "
                f"— Creada: {creation_date} — Fecha límite: {due_date_str}"
            )
        logger.info(
            f"Listando {len(tasks)} tareas del proyecto '{project or 'todos los proyectos'}'"
        )
        return task_list
    except Exception as e:
        logger.error(f"Error listando tareas del proyecto '{project}': {e}")
        return [f"Error al listar tareas: {str(e)}"]


def delete_task(task: str, project: str) -> str:
    """Elimina una tarea"""

    # Si el proyecto es None o vacío, usar proyecto por defecto
    if not project:
        logger.info(f"Proyecto no especificado, usando proyecto por defecto: '{DEFAULT_PROJECT}'")
        project = DEFAULT_PROJECT

    # Verificar si el proyecto existe
    if not projects_collection.find_one({"name": project}):
        if project == DEFAULT_PROJECT:
            logger.warning("Proyecto no especificado")
            return "No se especificó un proyecto."
        logger.warning(f"Proyecto '{project}' no encontrado")
        return f"No existe el proyecto '{project}'."

    try:
        result = tasks_collection.delete_one({
            "task": task, 
            "project": project
        })

        # Verificar si se eliminó alguna tarea
        if result.deleted_count == 0:
            logger.warning(f"Tarea '{task}' no encontrada en '{project}'")
            return f"No se encontró la tarea '{task}' en '{project}'."
        
        logger.info(f"Tarea '{task}' eliminada correctamente")
        return f"Tarea '{task}' eliminada correctamente."
    
    except Exception as e:
        logger.error(f"Error eliminando tarea '{task}': {e}")
        return f"Error al eliminar tarea: {str(e)}"


def update_task(task: str, project: str, priority: Optional[str] = None, due_date: Optional[datetime] = None) -> str:
    """Modifica los atributos de una tarea existente (prioridad y fecha de vencimiento)"""

    # Si el proyecto es None o vacío, usar proyecto por defecto
    if not project:
        logger.info(f"Proyecto no especificado, usando proyecto por defecto: '{DEFAULT_PROJECT}'")
        project = DEFAULT_PROJECT

    query = {"task": task, "project": project}
    update_fields = {}

    if priority is not None:
        update_fields["priority"] = priority
    if due_date is not None:
        update_fields["due_date"] = due_date
    if not update_fields:
        return "No se especificaron atributos para modificar."

    try:
        result = tasks_collection.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            return f"No se encontró la tarea '{task}' en el proyecto '{project}'."
        return f"Tarea '{task}' en proyecto '{project}' actualizada correctamente."
    
    except Exception as e:
        logger.error(f"Error actualizando tarea '{task}' en proyecto '{project}': {e}")
        return f"Error actualizando tarea: {str(e)}"


def execute_task_actions(actions: list) -> list:
    """Ejecuta una lista de acciones de tarea"""
    
    results = []
    for action in actions:
        order = action.get("order")
        task = action.get("task")
        project = action.get("project")
        priority = action.get("priority")
        due_date = action.get("due_date")
        if order == "create_task":
            results.append(create_task(task, project, priority, due_date))
        elif order == "close_task":
            results.append(close_task(task, project))
        elif order == "delete_task":
            results.append(delete_task(task, project))
        elif order == "list_tasks":
            results.extend(list_tasks(project, priority, due_date, action.get("completed")))
        elif order == "update_task":
            results.append(update_task(task, project, priority, due_date))
        else:
            results.append(f"Acción de tarea desconocida: {order}")
    return results
