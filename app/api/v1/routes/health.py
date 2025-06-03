from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    """
    Check the health status of the application.
    """
    try:
        # Add any health checks here (e.g., database connection, external services)
        return JSONResponse(
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "The Church Manager API"
            },
            status_code=200
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )
