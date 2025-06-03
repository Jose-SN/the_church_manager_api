import asyncio
import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.user import User, Role, Permission
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default permissions
PERMISSIONS = [
    {"name": "user:read", "description": "Read user information"},
    {"name": "user:write", "description": "Create/update users"},
    {"name": "user:delete", "description": "Delete users"},
    {"name": "role:read", "description": "Read role information"},
    {"name": "role:write", "description": "Create/update roles"},
    {"name": "role:delete", "description": "Delete roles"},
    {"name": "event:read", "description": "Read event information"},
    {"name": "event:write", "description": "Create/update events"},
    {"name": "event:delete", "description": "Delete events"},
]

# Default roles with permissions
ROLES = [
    {
        "name": "admin",
        "description": "Administrator with full access",
        "permissions": ["user:read", "user:write", "user:delete", 
                        "role:read", "role:write", "role:delete",
                        "event:read", "event:write", "event:delete"]
    },
    {
        "name": "pastor",
        "description": "Church pastor with event management access",
        "permissions": ["user:read", "event:read", "event:write"]
    },
    {
        "name": "member",
        "description": "Regular church member",
        "permissions": ["user:read", "event:read"]
    },
]

# Default admin user
ADMIN_USER = {
    "email": "admin@thechurchmanager.com",
    "full_name": "Admin User",
    "password": "changeme123",
    "is_active": True,
    "is_superuser": True,
    "roles": ["admin"]
}

async def init_permissions(session: AsyncSession) -> dict:
    """Initialize permissions in the database"""
    logger.info("Creating default permissions...")
    permissions = {}
    
    for perm_data in PERMISSIONS:
        result = await session.execute(
            select(Permission).where(Permission.name == perm_data["name"])
        )
        permission = result.scalars().first()
        
        if not permission:
            permission = Permission(**perm_data)
            session.add(permission)
            logger.info(f"Created permission: {perm_data['name']}")
        else:
            logger.info(f"Permission already exists: {perm_data['name']}")
        
        permissions[perm_data["name"]] = permission
    
    await session.commit()
    return permissions

async def init_roles(session: AsyncSession, permissions: dict) -> dict:
    """Initialize roles in the database"""
    logger.info("Creating default roles...")
    roles = {}
    
    for role_data in ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        role = result.scalars().first()
        
        if not role:
            role_perms = [permissions[name] for name in role_data["permissions"]]
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_perms
            )
            session.add(role)
            logger.info(f"Created role: {role_data['name']}")
        else:
            logger.info(f"Role already exists: {role_data['name']}")
        
        roles[role_data["name"]] = role
    
    await session.commit()
    return roles

async def init_admin_user(session: AsyncSession, roles: dict):
    """Initialize admin user"""
    logger.info("Creating admin user...")
    
    result = await session.execute(
        select(User).where(User.email == ADMIN_USER["email"])
    )
    user = result.scalars().first()
    
    if not user:
        user_roles = [roles[name] for name in ADMIN_USER["roles"]]
        user = User(
            email=ADMIN_USER["email"],
            full_name=ADMIN_USER["full_name"],
            hashed_password=get_password_hash(ADMIN_USER["password"]),
            is_active=ADMIN_USER["is_active"],
            is_superuser=ADMIN_USER["is_superuser"],
            roles=user_roles
        )
        session.add(user)
        logger.info("Created admin user")
    else:
        logger.info("Admin user already exists")
    
    await session.commit()

async def init() -> None:
    """Initialize database with default data"""
    logger.info("Initializing database...")
    
    async with async_session_factory() as session:
        try:
            # Initialize permissions
            permissions = await init_permissions(session)
            
            # Initialize roles with permissions
            roles = await init_roles(session, permissions)
            
            # Initialize admin user
            await init_admin_user(session, roles)
            
            logger.info("Database initialization completed successfully")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error initializing database: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(init())
