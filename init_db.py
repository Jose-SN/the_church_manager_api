#!/usr/bin/env python3
"""
Initialize the database with default data.
"""
import asyncio
import logging
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

async def init_db() -> bool:
    """Initialize the database with default data."""
    try:
        from scripts.init_db import main as init_db_script
        await init_db_script()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

async def create_test_data() -> bool:
    """Create test data in the database."""
    try:
        from scripts.create_test_data import main as create_test_data_script
        await create_test_data_script()
        return True
    except Exception as e:
        logger.error(f"Failed to create test data: {e}")
        return False

async def main():
    """Run the initialization."""
    logger.info("Initializing database...")
    
    # Initialize database with default data
    if not await init_db():
        logger.error("Failed to initialize database")
        sys.exit(1)
    
    # Create test data
    if not await create_test_data():
        logger.warning("Failed to create test data")
    
    logger.info("Database initialization completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
