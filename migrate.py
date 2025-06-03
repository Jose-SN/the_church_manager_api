#!/usr/bin/env python3
"""
Run database migrations.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

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
    """Run the migrations."""
    logger.info("Running database migrations...")
    
    if not await run_migrations():
        logger.error("Failed to run database migrations")
        sys.exit(1)
    
    logger.info("Database migrations completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
