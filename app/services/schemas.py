"""
Esquemas de datos para la API del agente de gestión de proyectos, tareas y eventos
"""

from typing import Annotated, List, Optional, Union, Literal
from pydantic import BaseModel, Field


# =========================================================
# Esquemas de proyectos
# =========================================================

class create_project(BaseModel):
    order: Literal["create_project"]
    project: str


class close_project(BaseModel):
    order: Literal["close_project"]
    project: str


class list_projects(BaseModel):
    order: Literal["list_projects"]


class delete_project(BaseModel):
    order: Literal["delete_project"]
    project: str


# =========================================================
# Esquemas de tareas
# =========================================================

class create_task(BaseModel):
    order: Literal["create_task"]
    task: str
    project: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


class close_task(BaseModel):
    order: Literal["close_task"]
    task: str
    project: Optional[str] = None


class list_tasks(BaseModel):
    order: Literal["list_tasks"]
    project: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None


class delete_task(BaseModel):
    order: Literal["delete_task"]
    task: str
    project: Optional[str] = None


class update_task(BaseModel):
    order: Literal["update_task"]
    task: str
    project: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None


# =========================================================
# Esquemas de eventos
# =========================================================

class create_event(BaseModel):
    order: Literal["create_event"]
    title: str
    datetime: str
    description: Optional[str] = None
    location: Optional[str] = None


class list_events(BaseModel):
    order: Literal["list_events"]
    before_date: Optional[str] = None


class update_event(BaseModel):
    order: Literal["update_event"]
    title: str
    datetime: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class delete_event(BaseModel):
    order: Literal["delete_event"]
    title: str


# =========================================================
# Esquema general de acción
# =========================================================


class BaseAction(BaseModel):
    order: str


Action = Annotated[
    Union[
    create_project,
    close_project,
    delete_project,
    list_projects,
    create_task,
    close_task,
    delete_task,
    update_task,
    list_tasks,
    create_event,
    list_events,
    update_event,
    delete_event
    ],
    Field(discriminator="order")
]


class ActionsResponse(BaseModel):
    actions: List[Action]