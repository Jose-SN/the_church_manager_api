#!/usr/bin/env python3
"""
Run the application in development mode.
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

def main():
    """Run the application."""
    # Set default environment variables
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    
    # Import uvicorn here to ensure environment variables are set first
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BASE_DIR / "app")],
        log_level="debug"
    )

if __name__ == "__main__":
    main()
