import asyncio
import logging
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the app directory is in the Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

def run_migrations() -> None:
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    # Get the directory containing this script
    script_location = BASE_DIR / "app" / "db" / "migrations"
    
    # Create the migrations directory if it doesn't exist
    os.makedirs(script_location, exist_ok=True)
    
    # Configure Alembic
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(script_location))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations completed successfully")

async def create_tables() -> None:
    """Create database tables"""
    logger.info("Creating database tables...")
    
    from app.db.base_class import Base
    from app.models import user, event  # noqa: F401
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")

async def main() -> None:
    """Main function to run migrations and create tables"""
    try:
        # Run migrations
        run_migrations()
        
        # Create tables if they don't exist
        await create_tables()
        
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
