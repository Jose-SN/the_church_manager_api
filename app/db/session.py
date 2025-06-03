from pymongo import MongoClient
from pymongo.database import Database
from typing import Generator
from app.core.config import settings

# MongoDB client
client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

# Dependency to get DB client
def get_db() -> Generator[Database, None, None]:
    """Dependency that provides a MongoDB client"""
    try:
        yield db
    finally:
        pass  # MongoDB client is connection pooled, no need to close explicitly
