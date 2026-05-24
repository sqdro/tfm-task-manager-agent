"""
Configuración de conexión a MongoDB
"""

from pymongo import MongoClient
from app.utils.logger import get_logger
from app.utils.config import MONGODB_URI, MONGODB_DB


logger = get_logger(__name__)


try:
    logger.info(f"Conectando a MongoDB: {MONGODB_URI}")
    client = MongoClient(MONGODB_URI)

    # Verificar conexión
    client.admin.command('ping')
    logger.info("Conexión a MongoDB exitosa")
    
    # Lista de colecciones disponibles
    db = client[MONGODB_DB]
    projects_collection = db["projects"]
    tasks_collection = db["tasks"]
    events_collection = db["events"]
    
except Exception as e:
    logger.error(f"Error al conectar con MongoDB: {e}")
    raise
