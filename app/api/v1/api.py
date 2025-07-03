from fastapi import APIRouter
from app.core.config import settings

from app.api.v1.routes import (
#     auth,
#     health,
#     status,
#     attendance,
#     event,
#     organization,
#     dashboard,
    meeting,
#     user,
)

api_router = APIRouter()

# Include all API endpoints
# Authentication
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# # User management
# api_router.include_router(user.router, prefix="/users", tags=["users"])

# # Other endpoints
# api_router.include_router(health.router, prefix="/health", tags=["health"])
# api_router.include_router(status.router, prefix="/status", tags=["status"])
# api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
# api_router.include_router(event.router, prefix="/events", tags=["events"])
# api_router.include_router(organization.router, prefix="/organizations", tags=["organizations"])
# api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(meeting.router, prefix="/meeting", tags=["meeting"])

# Add root endpoint
@api_router.get("/")
def root():
    """
    Root endpoint that returns API information
    """
    return {
        "name": "The Church Manager API",
        "version": settings.API_VERSION,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }
