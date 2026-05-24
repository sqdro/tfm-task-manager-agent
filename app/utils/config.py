"""
Configuración centralizada de la aplicación
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB")

# LLM
API_KEY = os.getenv("API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE"))

# Gradio
GRADIO_PORT = int(os.getenv("GRADIO_PORT"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL")
LOG_NAME = os.getenv("LOG_NAME")
