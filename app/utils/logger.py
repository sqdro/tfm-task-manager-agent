"""
Sistema de logging centralizado
"""

import logging
from pathlib import Path
import sys

from datetime import datetime
from app.utils.config import LOG_NAME, LOG_LEVEL


# Crear directorio de logs si no existe
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Crear nombre de archivo con timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"{LOG_NAME}_{timestamp}.log"


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado con el nombre especificado"""
    
    logger = logging.getLogger(name)
    
    # Evitar duplicados
    if logger.hasHandlers():
        return logger

    # Configuración del logger
    logger.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler fichero
    file_handler = logging.FileHandler(LOG_DIR / LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
