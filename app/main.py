from fastapi import FastAPI, Request
from app.api.v1.routes.attendance import router as attendance_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.user import router as user_router
from app.api.v1.routes.organization import router as organization_router
from app.api.v1.routes.dashboard import router as dashboard_router
from app.api.v1.routes.analytics import router as analytics_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.logger import logger
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import uvicorn
import logging
import json

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging_config import LogConfig
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.core.security import get_current_active_user

# Configure logging
logging.config.dictConfig(LogConfig().dict())
logger = logging.getLogger("the_church_manager")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Custom docs endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}

# Custom error handler
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    logger.error(f"An error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

# Database connection events
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    logger.info("Application startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    logger.info("Application shutdown complete")

# Custom OpenAPI schema
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(
        json.loads(
            json.dumps(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    description=app.description,
                    routes=app.routes,
                )
            )
        )
    )

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )