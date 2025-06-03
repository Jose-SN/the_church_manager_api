#!/usr/bin/env python3
"""
Run tests with pytest.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

def run_tests() -> int:
    """Run pytest and return the exit code."""
    # Set test environment variables
    os.environ["TESTING"] = "True"
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_church_manager"
    )
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--asyncio-mode=auto",
        "-v",
        "tests/"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
