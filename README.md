# TFM Task Manager Agent

> Agente inteligente para gestión de proyectos, tareas y eventos de calendario.

## Descripción

Este repositorio contiene un agente de asistencia personal que interpreta instrucciones en lenguaje natural y realiza acciones de gestión sobre:

- Proyectos
- Tareas
- Eventos de calendario

La aplicación usa Gradio como interfaz web, MongoDB para persistencia y LangChain para la interpretación de texto. Además, utiliza LangGraph para orquestar el flujo de ejecución entre interpretación y acción.

## Características principales

- Interpretación de comandos en lenguaje natural
- Gestión de proyectos, tareas y eventos
- Generación de enlaces para Google Calendar
- Persistencia en MongoDB
- Interfaz web con Gradio
- Orquestación de flujo con LangGraph
- Interpretación y contexto con LangChain

## Tecnologías clave

- **LangGraph**: organiza el flujo de trabajo del agente como un grafo de estados con nodos de interpretación y ejecución. Esto separa la fase de comprensión del texto de la fase de acción.
- **LangChain**: se usa para interactuar con el LLM, construir prompts estructurados y generar salidas tipadas. El servicio LLM crea mensajes de tipo `HumanMessage` y aplica `ChatPromptTemplate` para dar contexto y formato al modelo.
- **Mini-RAG**: el servicio LLM recupera contexto relevante desde MongoDB usando embeddings. `build_relevant_db_context` compara la consulta del usuario con embeddings de proyectos, tareas y eventos y filtra aquellos que sean de utilidad para facilitar la comprensión del LLM.

## Estructura del proyecto

```
tfm-task-manager-agent/
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── interfaces/
│   │   └── gradio_app.py
│   ├── persistence/
│   │   └── database.py
│   ├── services/
│   │   ├── calendar_service.py
│   │   ├── event_service.py
│   │   ├── llm_service.py
│   │   ├── project_service.py
│   │   ├── schemas.py
│   │   └── task_service.py
│   ├── utils/
│   │   ├── config.py
│   │   └── logger.py
│   └── __main__.py
├── docker/
│   └── Dockerfile
├── logs/
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## Requisitos

- Python 3.12+
- MongoDB
- OpenAI API key

## Configuración

Copia el archivo de ejemplo `.env.example` y define tus valores:

Ejemplo de `.env`:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=tfm_task_manager
API_KEY=
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.0
GRADIO_PORT=7860
LOG_LEVEL=INFO
LOG_NAME=tfm_task_manager_agent
```

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

### Iniciar la aplicación

```bash
python -m app
```

## Cómo funciona

1. El usuario ingresa texto en la interfaz Gradio.
2. `app.agent.graph` construye un `StateGraph` de LangGraph con el tipo de estado `AgentState`.
3. El nodo `interpret` en `app.agent.nodes` llama a `app.services.llm_service.text_interpretation`.
   - LangChain crea un prompt con `ChatPromptTemplate` y mensajes de conversación (`HumanMessage` / `AIMessage`).
   - Se recupera contexto relevante desde MongoDB con `build_relevant_db_context` usando embeddings de proyectos, tareas y eventos.
   - El modelo OpenAI se llama mediante `ChatOpenAI` y su salida estructurada se valida con `ActionsResponse` de Pydantic.
4. El nodo `execute` recibe las acciones interpretadas y enruta cada orden al servicio correspondiente (`project_service`, `task_service`, `event_service`).
5. Cada servicio aplica la operación en MongoDB y devuelve mensajes en lenguaje natural.
6. La respuesta final se muestra en Gradio y se agrega al historial de conversación.

## Órdenes disponibles

### Proyectos

- `create_project`: crea un nuevo proyecto en la base de datos.
- `close_project`: marca un proyecto como cerrado sin eliminarlo.
- `list_projects`: lista todos los proyectos existentes.
- `delete_project`: elimina un proyecto y sus tareas asociadas.

### Tareas

- `create_task`: crea una nueva tarea dentro de un proyecto.
- `close_task`: marca una tarea como completada.
- `list_tasks`: lista tareas con filtros opcionales (proyecto, prioridad, fecha, completadas).
- `delete_task`: elimina una tarea específica.
- `update_task`: actualiza atributos de una tarea, como prioridad o fecha límite.

### Eventos

- `create_event`: crea un nuevo evento de calendario.
- `list_events`: lista eventos programados, opcionalmente filtrando por fecha.
- `update_event`: actualiza detalles de un evento existente.
- `delete_event`: elimina un evento de calendario.

## Ejemplos de uso

- "Crear un proyecto llamado 'TFM'"
- "Añadir una tarea de 'Implementación de un agente conversacional' para la próxima semana"
- "Listar todas las tareas pendientes"
- "Programar un evento 'Defensa TFM' para el 25 de junio"

## Módulos principales

- `app/__main__.py`: punto de entrada principal.
- `app/interfaces/gradio_app.py`: interfaz de usuario Gradio.
- `app/agent/graph.py`: construcción del flujo LangGraph.
- `app/agent/nodes.py`: nodos de interpretación y ejecución.
- `app/agent/state.py`: estado del agente.
- `app/services/llm_service.py`: interpretación LLM y mini-RAG.
- `app/services/project_service.py`: gestión de proyectos.
- `app/services/task_service.py`: gestión de tareas.
- `app/services/event_service.py`: gestión de eventos.
- `app/services/calendar_service.py`: generación de enlaces Google Calendar.
- `app/services/schemas.py`: esquemas de acciones con Pydantic.
- `app/persistence/database.py`: conexión MongoDB.
- `app/utils/config.py`: carga de configuración.
- `app/utils/logger.py`: logging a consola y fichero.

## Notas importantes

- El servicio LLM requiere que `API_KEY` esté configurada.
- Si falta la clave, el agente no podrá inicializar el modelo y no procesará solicitudes.
- Los datos se guardan en las colecciones `projects`, `tasks` y `events`.
- Los logs se generan en `logs/`.
