#!/usr/bin/env python3
"""
Generate API documentation using OpenAPI and ReDoc.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

def generate_openapi_json() -> Dict[str, Any]:
    """Generate OpenAPI JSON schema."""
    from app.main import app
    
    # Generate OpenAPI schema
    openapi_schema = app.openapi()
    
    # Save to file
    docs_dir = BASE_DIR / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    openapi_path = docs_dir / "openapi.json"
    with open(openapi_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"OpenAPI schema saved to {openapi_path}")
    return openapi_schema

def generate_redoc_html() -> None:
    """Generate ReDoc HTML documentation."""
    from jinja2 import Environment, FileSystemLoader
    
    # Set up Jinja2 environment
    templates_dir = BASE_DIR / "app" / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    # Render template
    template = env.get_template("redoc.html")
    html = template.render(
        title="The Church Manager API",
        openapi_url="/openapi.json"
    )
    
    # Save to file
    docs_dir = BASE_DIR / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    redoc_path = docs_dir / "index.html"
    with open(redoc_path, "w") as f:
        f.write(html)
    
    print(f"ReDoc documentation saved to {redoc_path}")

def main() -> int:
    """Main function."""
    try:
        # Generate OpenAPI JSON
        generate_openapi_json()
        
        # Generate ReDoc HTML
        generate_redoc_html()
        
        print("\nDocumentation generation complete!")
        return 0
    except Exception as e:
        print(f"Error generating documentation: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
