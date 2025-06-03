import uvicorn
from pathlib import Path
import sys

# Add the app directory to the Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(BASE_DIR / "app")],
        workers=1
    )
