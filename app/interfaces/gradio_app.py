"""
Interfaz Gradio para el agente de gestión de proyectos, tareas y eventos de calendario
"""

import gradio as gr
from app.agent.graph import build_graph
from app.utils.logger import get_logger
from app.utils.config import GRADIO_PORT


logger = get_logger(__name__)

# Construir el grafo del agente al iniciar la aplicación
graph = build_graph()
chat_history = []


def user_chat_handler(user_text: str) -> tuple:
    '''Maneja la interacción del usuario con el agente a través de Gradio'''

    if not user_text or not user_text.strip():
        return "Por favor, escriba un mensaje.", format_history(chat_history)

    try:
        logger.info("=" * 60)

        # Se envían las últimas 5 interacciones para mantener contexto
        history_state = [
            {"user": turn[0], "assistant": turn[1]}
            for turn in chat_history[-5:]
        ]

        # Invocar el grafo del agente con el mensaje del usuario y el historial
        agent_result = graph.invoke({"input": user_text, "history": history_state})
        agent_response = agent_result.get("result", "Error procesando la solicitud")

        logger.info(f"Respuesta generada: {agent_response}")

        response_text = agent_response

        if isinstance(agent_response, list):
            # Si la respuesta es una lista, se formatea para mostrar cada elemento en una nueva línea
            response_text = "\n\n".join(f"- {str(item)}" for item in agent_response)
        elif isinstance(agent_response, str):
            # Si viene todo en una sola línea, se intenta separar
            response_text = agent_response.replace(" [", "\n\n[")
        else:
            response_text = str(agent_response)

        # Agregar la interacción al historial
        chat_history.append((user_text, response_text))

        return response_text, format_history(chat_history)

    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        return f"Error: {str(e)}", format_history(chat_history)


def format_history(history):
    """Formatea el historial de conversación para mostrarlo en Markdown"""

    if not history:
        return ""

    lines = ["## Historial de conversación:\n"]

    for i, (user, agent) in enumerate(history, 1):
        lines.append(f"**[{i}] Usuario:** {user}")
        lines.append("")
        lines.append(f"**[{i}] Agente:** {agent}")
        lines.append("")

    return "\n".join(lines)


def main():
    """Función principal para iniciar la interfaz Gradio"""

    logger.info("Iniciando interfaz Gradio...")

    with gr.Blocks(title="Agente de Gestión de Proyectos, Tareas y Eventos de Calendario") as iface:
        gr.Markdown("# Agente de Gestión de Proyectos, Tareas y Eventos de Calendario")

        # Área de entrada para el mensaje del usuario
        user_input = gr.Textbox(
            label="Mensaje",
            placeholder="Describe lo que quieres hacer...",
            lines=2
        )

        # Botón para enviar el mensaje al agente
        submit_btn = gr.Button("Enviar")

        # Ejemplos predefinidos para guiar al usuario
        gr.Examples(
            [
                ["Lista todos los proyectos"],
                ["Lista todas las tareas"],
                ["Lista todos los eventos"]
            ],
            inputs=[user_input]
        )

        gr.Markdown("---")
        gr.Markdown("## Respuesta:")

        # Área para mostrar la respuesta del agente
        agent_output = gr.Markdown(label="Respuesta")

        gr.Markdown("---")

        # Área para mostrar el historial de conversación
        history_output = gr.Markdown("", elem_id="chat-history")

        iface.stylesheet = """
        #chat-history {
            font-size: 0.85em;
            line-height: 1.2em;
            margin-top: 0.15em;
        }
        """

        # Configurar eventos del botón
        submit_btn.click(
            user_chat_handler,
            inputs=user_input,
            outputs=[agent_output, history_output]
        )

        # Permitir enviar el mensaje presionando Enter
        user_input.submit(
            user_chat_handler,
            inputs=user_input,
            outputs=[agent_output, history_output]
        )

    logger.info(f"Lanzando servidor en puerto {GRADIO_PORT}")
    iface.launch(server_port=GRADIO_PORT)


if __name__ == "__main__":
    main()