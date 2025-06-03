#!/usr/bin/env python3
"""
Start the FastAPI application with proper logging and error handling.
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn

# Configure logging before importing other modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

# Import after path is set
from app.core.config import settings

class Server:
    """Server control for graceful shutdown."""
    
    def __init__(self):
        self.should_exit = False
        self.server = None
        
    def handle_exit(self, sig, frame):
        """Handle shutdown signals."""
        self.should_exit = True
        if self.server:
            self.server.should_exit = True

def check_environment() -> bool:
    """Check if all required environment variables are set."""
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "FIRST_SUPERUSER_EMAIL",
        "FIRST_SUPERUSER_PASSWORD",
    ]
    
    missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

async def run_migrations() -> bool:
    """Run database migrations."""
    try:
        from scripts.migrate import run_migrations as run_migrations_script
        run_migrations_script()
        return True
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        return False

async def main():
    """Run the application."""
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run migrations
    if not await run_migrations():
        logger.error("Failed to run database migrations")
        sys.exit(1)
    
    # Configure server
    config = uvicorn.Config(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
        reload_dirs=[str(BASE_DIR / "app")] if settings.DEBUG else None,
    )
    
    server = Server()
    signal.signal(signal.SIGINT, server.handle_exit)
    signal.signal(signal.SIGTERM, server.handle_exit)
    
    # Start server
    try:
        logger.info(f"Starting server on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        logger.info("Server stopped")

if __name__ == "__main__":
    asyncio.run(main())
