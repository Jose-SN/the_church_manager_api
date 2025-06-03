#!/usr/bin/env python3
"""
Set up the development environment.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

def run_command(cmd: list, cwd: Path = None) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd or BASE_DIR)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def setup_python_environment() -> bool:
    """Set up the Python virtual environment."""
    venv_dir = BASE_DIR / ".venv"
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", ".venv"]):
            return False
    
    # Install dependencies
    print("Installing dependencies...")
    pip_cmd = [
        str(venv_dir / "bin" / "pip") if os.name != "nt" else str(venv_dir / "Scripts" / "pip"),
        "install",
        "-r", "requirements/dev.txt"
    ]
    
    if not run_command(pip_cmd):
        return False
    
    return True

def setup_git_hooks() -> bool:
    """Set up Git hooks."""
    hooks_dir = BASE_DIR / ".git" / "hooks"
    
    if not hooks_dir.exists():
        print("Git hooks directory not found. Is this a Git repository?")
        return False
    
    # Create pre-commit hook
    pre_commit = hooks_dir / "pre-commit"
    if not pre_commit.exists():
        print("Creating pre-commit hook...")
        pre_commit.write_text(
            "#!/bin/sh\n"
            "echo 'Running pre-commit checks...'\n"
            "python -m black --check .\n"
            "python -m isort --check-only .\n"
            "python -m flake8 .\n"
            "python -m mypy .\n"
        )
        pre_commit.chmod(0o755)
    
    return True

def main() -> int:
    """Main function."""
    print("Setting up development environment...")
    
    if not setup_python_environment():
        print("Failed to set up Python environment")
        return 1
    
    if not setup_git_hooks():
        print("Warning: Failed to set up Git hooks")
    
    print("\nDevelopment environment setup complete!")
    print("To activate the virtual environment, run:")
    print(f"  source {BASE_DIR}/.venv/bin/activate  # Linux/macOS")
    print(f"  {BASE_DIR}\\.venv\\Scripts\\activate  # Windows")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
