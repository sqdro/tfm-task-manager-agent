"""
TFM Task Manager Agent - Agente de asistencia personal basado en LLM
Gestión inteligente de proyectos, tareas y eventos de calendario
"""

from app.utils.logger import get_logger
from app.interfaces.gradio_app import main

# Inicializar logger para la aplicación
logger = get_logger(__name__)

if __name__ == '__main__':
    logger.info('TFM Task Manager Agent en ejecución...')
    main()