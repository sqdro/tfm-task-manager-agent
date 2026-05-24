"""
Servicio de interpretación de texto libre a acciones estructuradas
Utiliza un modelo LLM para convertir mensajes de usuario en órdenes específicas
"""

import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)
from langchain_core.prompts import ChatPromptTemplate

from app.utils.logger import get_logger
from app.utils.config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    API_KEY,
)

from app.persistence.database import (
    events_collection,
    projects_collection,
    tasks_collection,
)

from app.services.schemas import (
    ActionsResponse,
)


logger = get_logger(__name__)


# =========================================================
# Inicializar modelo
# =========================================================

current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")

llm = None
structured_llm = None

try:

    if not API_KEY:
        raise ValueError("API_KEY no está configurada")

    # Cargar modelo LLM
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=API_KEY,
    )

    # Configurar salida estructurada
    structured_llm = llm.with_structured_output(ActionsResponse)

    # Cargar modelo de embeddings para recuperación de contexto relevante mediante mini-RAG
    embeddings_model = OpenAIEmbeddings(
        api_key=API_KEY,
        model="text-embedding-3-small"
    )

    logger.info(f"Modelo ChatOpenAI cargado: {LLM_MODEL}")

except Exception as e:
    logger.error(f"Error al cargar modelo OpenAI: {e}")


# =========================================================
# Prompt
# =========================================================

SYSTEM_PROMPT = """
You are a smart personal management assistant.
Your function is to interpret user messages and convert them into structured actions.

You manage:
- projects:
    - create_project: create new project
    - close_project: close existing project without deleting it
    - list_projects: list active projects
    - delete_project: delete existing project
- task:
    - create_task: create new task
    - close_task: mark task as completed without deleting it
    - list_tasks: list active tasks (optionally by project, priority, due_date, completed)
    - delete_task: delete existing task
    - update_task: update fields of existing task (project, priority, due_date)
- calendar events (event):
    - create_event: create new event
    - list_events: list upcoming events (optionally before a date)
    - update_event: update fields of existing event (datetime, description, location)
    - delete_event: delete existing event

You must:
1. Identify intent (task, project, event)
2. Select exact available action, order must be one of the specified above (e.g. create_project, list_tasks, update_event, etc.)
3. You must always format all datetime values using "YYYY-MM-DD HH:MM" format
4. Validate data with context
5. Never invent data
6. If information is missing, use null
7. If there is ambiguity, prioritize query (list_*)
8. Task priority must be one of the following values only: low, medium, high
"""

prompt_template = ChatPromptTemplate.from_messages([
    (
        "system",
        SYSTEM_PROMPT,
    ),
    (
        "human",
        """
Current datetime: 
{current_datetime}

Relevant context from the database:
{db_context}

Current user message:
{user_text}
"""
    ),
])


# =========================================================
# Funciones auxiliares para recuperación de contexto relevante (mini-RAG)
# =========================================================

def get_embedding(text: str) -> list[float]:
    """Obtiene el embedding de un texto"""
    return embeddings_model.embed_query(text)


def cosine_similarity(a, b):
    """Calcula la similitud coseno entre dos vectores"""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_relevant_db_context(user_text: str, top_k: int = 5) -> Dict[str, List[Dict[str, Any]]]:    
    """Recupera contexto relevante para facilitar la interpretación del agente"""

    # Obtener embedding de la consulta del usuario
    query_embedding = get_embedding(user_text)

    results = {
        "projects": [],
        "tasks": [],
        "events": []
    }

    # -------------------------
    # Proyectos
    # -------------------------

    # Obtener todos los proyectos con sus embeddings
    projects = projects_collection.find({}, {"name": 1, "embedding": 1})

    scored_projects = []
    for p in projects:

        # Calcular similitud coseno entre el embedding de la consulta y el embedding del proyecto
        score = cosine_similarity(query_embedding, p["embedding"])
        scored_projects.append((score, p))

    scored_projects.sort(reverse=True, key=lambda x: x[0])

    # Agregar los proyectos más relevantes al contexto (top_k)
    results["projects"] = [
        {"name": p["name"], "score": s}
        for s, p in scored_projects[:top_k]
    ]

    # -------------------------
    # Tareas
    # -------------------------

    # Obtener todas las tareas con sus embeddings
    tasks = tasks_collection.find({}, {"task": 1, "embedding": 1, "project": 1})

    scored_tasks = []
    for t in tasks:

        # Calcular similitud coseno entre el embedding de la consulta y el embedding de la tarea
        score = cosine_similarity(query_embedding, t["embedding"])
        scored_tasks.append((score, t))

    scored_tasks.sort(reverse=True, key=lambda x: x[0])

    # Agregar las tareas más relevantes al contexto (top_k)
    results["tasks"] = [
        {
            "task": t["task"],
            "project": t.get("project"),
            "score": s
        }
        for s, t in scored_tasks[:top_k]
    ]

    # -------------------------
    # Eventos de calendario
    # -------------------------

    # Obtener todos los eventos con sus embeddings
    events = events_collection.find({}, {"title": 1, "embedding": 1})

    scored_events = []
    for e in events:

        # Calcular similitud coseno entre el embedding de la consulta y el embedding del evento
        score = cosine_similarity(query_embedding, e["embedding"])
        scored_events.append((score, e))

    scored_events.sort(reverse=True, key=lambda x: x[0])

    # Agregar los eventos más relevantes al contexto (top_k)
    results["events"] = [
        {"title": e["title"], "score": s}
        for s, e in scored_events[:top_k]
    ]

    return results


def build_conversation_messages(history: Optional[List[Dict[str, str]]]) -> List:
    """Construye mensajes de conversación a partir del historial para proporcionar contexto al LLM"""

    messages = []

    if not history:
        return messages

    for turn in history[-10:]:

        # Extraer mensaje de usuario y asistente
        user_msg = turn.get("user")
        assistant_msg = turn.get("assistant")

        # Agregar mensajes al contexto
        if user_msg:
            messages.append(HumanMessage(content=user_msg))
        if assistant_msg:
            messages.append(AIMessage(content=assistant_msg))

    return messages


# =========================================================
# Función principal de interpretación de texto a acciones estructuradas
# =========================================================

def text_interpretation(
    user_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, Any]]:
    """
    Interpreta texto libre y genera acciones estructuradas"""

    if not structured_llm:
        logger.error("LLM no disponible")
        return []

    try:

        # =================================================
        # Recuperar contexto relevante de la base de datos (mini-RAG)
        # =================================================

        db_context = (build_relevant_db_context(user_text))

        # =================================================
        # Prompt
        # =================================================

        prompt_messages = (
            prompt_template.format_messages(
                current_datetime=current_datetime,
                db_context=db_context,
                user_text=user_text
            )
        )

        # =================================================
        # Historial conversacional
        # =================================================

        history_messages = (build_conversation_messages(conversation_history))

        # =================================================
        # Mensajes finales
        # =================================================

        messages = [*history_messages,*prompt_messages,]

        logger.info("============ Input LLM ============")
        logger.info(f"Mensaje usuario: {user_text}")

        # =================================================
        # Structured Output
        # =================================================

        response: ActionsResponse = (
            structured_llm.invoke(
                messages
            )
        )

        logger.info("============ Output LLM ============")
        logger.info(f"Respuesta LLM: {response}")

        # =================================================
        # Resultado final
        # =================================================

        result = [action.model_dump() for action in response.actions]

        return result

    except Exception as e:
        logger.error(f"Error interpretando texto: {e}",exc_info=True,)
        return []