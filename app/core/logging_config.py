from pydantic import BaseModel
from typing import Dict, Any
import logging
import sys
from pathlib import Path
from app.core.config import settings

class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""
    
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = settings.LOG_LEVEL
    LOG_FILE: str = "app.log"
    LOG_DIR: str = "logs"
    
    # Create logs directory if it doesn't exist
    LOG_DIR_PATH = Path(LOG_DIR)
    LOG_DIR_PATH.mkdir(parents=True, exist_ok=True)
    
    LOG_FILE_PATH = LOG_DIR_PATH / LOG_FILE
    
    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(LOG_FILE_PATH),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        "the_church_manager": {
            "handlers": ["default", "file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["default", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["default", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    }