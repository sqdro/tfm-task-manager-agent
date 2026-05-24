"""
Orquestación del agente LangGraph definiendo el flujo de ejecución
"""

from langgraph.graph import StateGraph
from app.agent.state import AgentState
from app.agent.nodes import interpret, execute
from app.utils.logger import get_logger


logger = get_logger(__name__)


def create_agent_graph():
    """
    Construye el grafo del agente LangGraph
    
    El grafo define el flujo de ejecución:
    1. Interpret: Convierte el texto en una estructura interpretable en formato JSON
    2. Execute: Realiza la acción solicitada según la interpretación previa
    """

    logger.info("Construyendo grafo del agente...")
    
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    workflow.add_node("interpret", interpret)
    workflow.add_node("execute", execute)
    
    # Establecer punto de entrada y transiciones
    workflow.set_entry_point("interpret")
    workflow.add_edge("interpret", "execute")
    
    # Compilar el grafo
    graph = workflow.compile()
    logger.info("Grafo del agente construido exitosamente")
    
    return graph


def build_graph():
    """Construye y devuelve el grafo del agente"""
    return create_agent_graph()