from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import Base, engine, async_session_factory
from app.models.user import User
from app.core.security import get_password_hash

async def init_db() -> None:
    """Initialize the database with required tables and data"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Create default admin user if it doesn't exist
    async with async_session_factory() as db:
        from app.services.user_service import UserService
        
        # Check if admin user exists
        user_service = UserService(db)
        admin_user = await user_service.get_by_email(settings.FIRST_SUPERUSER_EMAIL)
        
        if not admin_user:
            # Create admin user
            admin_data = {
                "email": settings.FIRST_SUPERUSER_EMAIL,
                "password": settings.FIRST_SUPERUSER_PASSWORD,
                "full_name": "Admin User",
                "is_superuser": True,
                "is_active": True
            }
            await user_service.create(admin_data)
            print("Created default admin user")

async def clear_db() -> None:
    """Drop all tables (for testing)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
