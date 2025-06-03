from pydantic_settings import BaseSettings
from typing import List, Optional, Any, Dict, Union
from pydantic import AnyHttpUrl, validator, PostgresDsn, field_validator
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "The Church Manager API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Server settings
    SERVER_NAME: str = "localhost"
    SERVER_HOST: AnyHttpUrl = "http://localhost:8000"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Default React port
        "http://localhost:8000",  # Default FastAPI port
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "the_church_manager"
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "noreply@thechurchmanager.com"
    EMAILS_FROM_NAME: Optional[str] = "The Church Manager"
    
    # Security
    FIRST_SUPERUSER: str = "admin@thechurchmanager.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"
    
    # File upload settings
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS: set = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create uploads directory if it doesn't exist
os.makedirs(Settings().UPLOAD_FOLDER, exist_ok=True)

# Create instance
settings = Settings()

# For dependency injection
@lru_cache()
def get_settings() -> Settings:
    return Settings()