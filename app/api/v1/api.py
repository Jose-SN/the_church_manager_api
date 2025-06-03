from fastapi import APIRouter

from app.api.v1.endpoints import (
    user, 
    health, 
    status, 
    attendance, 
    event, 
    organization, 
    dashboard,
    auth,
    users as users_endpoint
)

api_router = APIRouter()

# Include all API endpoints
# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User management
api_router.include_router(users_endpoint.router, prefix="/users", tags=["users"])

# Other endpoints
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(event.router, prefix="/events", tags=["events"])
api_router.include_router(organization.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Add root endpoint
@api_router.get("/")
async def root():
    """
    Root endpoint that returns API information
    """
    return {
        "name": "The Church Manager API",
        "version": "1.0.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }
