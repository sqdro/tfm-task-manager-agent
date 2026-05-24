"""
Nodos del grafo del agente
"""

from app.services import event_service, llm_service, project_service, task_service


def interpret(state):
    """Nodo de interpretación: convierte el texto en un json interpretable por el agente"""

    user_text = state["input"]
    conversation_history = state.get("history", [])
    state["parsed_json"] = llm_service.text_interpretation(user_text, conversation_history)
    
    return state


def execute(state):
    """Nodo de ejecución: realiza la acción solicitada según la interpretación previa"""

    parsed_response = state["parsed_json"]
    
    results = []
    for action in parsed_response:
        order = action.get("order")
        # Acciones de proyecto
        if order in ["create_project", "close_project", "list_projects", "delete_project"]:
            results.extend(project_service.execute_project_actions([action]))
        # Acciones de tarea
        elif order in ["create_task", "close_task", "list_tasks", "delete_task", "update_task"]:
            results.extend(task_service.execute_task_actions([action]))
        # Acciones de evento de calendario
        elif order in ["create_event", "list_events", "update_event", "delete_event"]:
            results.extend(event_service.execute_event_actions([action]))
        else:
            results.append("Acción no reconocida.")
    state["result"] = results

    return state