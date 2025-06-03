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
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

async def run_script(script_name: str) -> bool:
    """Run a Python script and return True if successful"""
    import importlib
    from importlib import util
    
    script_path = BASE_DIR / "scripts" / f"{script_name}.py"
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running {script_name}...")
    
    try:
        spec = util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "main") and asyncio.iscoroutinefunction(module.main):
            await module.main()
        elif hasattr(module, "main"):
            module.main()
        else:
            logger.error(f"Script {script_name} has no 'main' function")
            return False
            
        logger.info(f"{script_name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}", exc_info=True)
        return False

async def main():
    """Run all initialization steps"""
    # 1. Run database migrations
    success = await run_script("migrate")
    if not success:
        logger.error("Database migration failed")
        sys.exit(1)
    
    # 2. Initialize database with default data
    success = await run_script("init_db")
    if not success:
        logger.error("Database initialization failed")
        sys.exit(1)
    
    # 3. Create test data
    success = await run_script("create_test_data")
    if not success:
        logger.warning("Test data creation failed or was skipped")
    
    logger.info("Initialization completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
