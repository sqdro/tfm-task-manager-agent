"""
Servicio de gestión de proyectos
"""

from typing import List
from datetime import datetime
from app.persistence.database import projects_collection, tasks_collection
from app.services.llm_service import get_embedding
from app.utils.logger import get_logger


logger = get_logger(__name__)


def create_project(name: str) -> str:
    """Crea un nuevo proyecto si no existe"""

    if not name or not name.strip():
        logger.warning("Intento de crear proyecto con nombre vacío")
        return "El nombre del proyecto no puede estar vacío."
    
    if projects_collection.find_one({"name": name}):
        logger.info(f"Proyecto '{name}' ya existe")
        return f"El proyecto '{name}' ya existe."
    
    try:
        project = {"name": name, "embedding": get_embedding(name), "status": "open", "created_at": datetime.now()}
        result = projects_collection.insert_one(project)
        logger.info(f"Proyecto '{name}' creado correctamente (ID: {result.inserted_id})")
        return f"Proyecto '{name}' creado correctamente."
    
    except Exception as e:
        logger.error(f"Error creando proyecto '{name}': {e}")
        return f"Error al crear proyecto: {str(e)}"


def close_project(name: str) -> str:
    """Cierra un proyecto existente"""

    try:
        result = projects_collection.update_one(
            {"name": name}, {"$set": {"status": "closed"}}
        )

        if result.matched_count == 0:
            logger.warning(f"Proyecto '{name}' no encontrado")
            return f"No se encontró el proyecto '{name}'."
        
        logger.info(f"Proyecto '{name}' cerrado correctamente")
        return f"Proyecto '{name}' cerrado correctamente."
    
    except Exception as e:
        logger.error(f"Error cerrando proyecto '{name}': {e}")
        return f"Error al cerrar proyecto: {str(e)}"


def list_projects(silent: bool = False) -> List[str]:
    """Lista todos los proyectos disponibles"""

    try:
        projects = list(projects_collection.find())

        if not projects:
            if not silent:
                logger.info("No hay proyectos disponibles")
            return ["No hay proyectos disponibles."]
        
        project_list = [
            f"{p['name']} — Estado: {p['status']} — Creado: {p['created_at'].strftime('%d/%m/%Y %H:%M')}"
            for p in projects
        ]
        if not silent:
            logger.info(f"Listando {len(projects)} proyectos")
        return project_list
    
    except Exception as e:
        logger.error(f"Error listando proyectos: {e}")
        return [f"Error al listar proyectos: {str(e)}"]


def delete_project(name: str) -> str:
    """Elimina un proyecto y todas sus tareas asociadas"""

    try:
        task_result = tasks_collection.delete_many({"project": name})
        project_result = projects_collection.delete_one({"name": name})

        if project_result.deleted_count == 0:
            logger.warning(f"Proyecto '{name}' no encontrado para eliminar")
            return f"No se encontró el proyecto '{name}'."
        logger.info(f"Proyecto '{name}' y {task_result.deleted_count} tareas eliminadas correctamente")
        return f"Proyecto '{name}' y {task_result.deleted_count} tareas eliminadas correctamente."
    
    except Exception as e:
        logger.error(f"Error eliminando proyecto '{name}': {e}")
        return f"Error al eliminar proyecto: {str(e)}"


def execute_project_actions(actions: list) -> list:
    """Ejecuta una lista de acciones de proyecto"""
    
    results = []
    for action in actions:
        order = action.get("order")
        name = action.get("project")
        if order == "create_project":
            results.append(create_project(name))
        elif order == "close_project":
            results.append(close_project(name))
        elif order == "delete_project":
            results.append(delete_project(name))
        elif order == "list_projects":
            results.extend(list_projects())
        else:
            results.append(f"Acción de proyecto desconocida: {order}")
    return results
