#!/usr/bin/env python3
"""
Format code using black and isort.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

def run_command(cmd: list) -> int:
    """Run a shell command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1

def format_code() -> int:
    """Format code using black and isort."""
    # Run black
    black_cmd = ["black", "app", "tests", "scripts", "migrations"]
    if run_command(black_cmd) != 0:
        return 1
    
    # Run isort
    isort_cmd = ["isort", "app", "tests", "scripts", "migrations"]
    if run_command(isort_cmd) != 0:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(format_code())
