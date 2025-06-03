#!/usr/bin/env python3
"""
Check code quality using flake8, mypy, and black.
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

def check_code_quality() -> int:
    """Check code quality using various tools."""
    # Run flake8
    flake8_cmd = ["flake8", "app", "tests", "scripts", "migrations"]
    if run_command(flake8_cmd) != 0:
        return 1
    
    # Run mypy
    mypy_cmd = ["mypy", "app", "tests", "scripts", "migrations"]
    if run_command(mypy_cmd) != 0:
        return 1
    
    # Run black in check mode
    black_cmd = ["black", "--check", "app", "tests", "scripts", "migrations"]
    if run_command(black_cmd) != 0:
        print("\nCode is not formatted. Run 'python format.py' to fix formatting.", file=sys.stderr)
        return 1
    
    # Run isort in check mode
    isort_cmd = ["isort", "--check-only", "app", "tests", "scripts", "migrations"]
    if run_command(isort_cmd) != 0:
        print("\nImports are not sorted. Run 'python format.py' to fix imports.", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(check_code_quality())
