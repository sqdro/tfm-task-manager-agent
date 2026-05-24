"""
Definición del estado del agente
"""

from typing import Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    input: str                              # Mensaje del usuario que será procesado por el agente
    history: Optional[List[Dict[str, str]]] # Historial reciente de la conversación
    parsed_json: Optional[List[dict]]       # JSON resultante de interpretar la entrada
    result: Optional[str]                   # Resultado de la acción ejecutada
