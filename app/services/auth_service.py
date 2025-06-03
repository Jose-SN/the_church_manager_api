from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import UserService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Get password hash"""
    return pwd_context.hash(password)

async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate user"""
    user_service = UserService(db)
    user = await user_service.get_by_email(email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(
    db: AsyncSession, token: str
) -> Optional[User]:
    """Get current user from token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        return None
    
    user_service = UserService(db)
    user = await user_service.get(int(token_data.sub))
    if user is None:
        return None
    return user

async def get_current_active_user(
    db: AsyncSession, token: str
) -> Optional[User]:
    """Get current active user"""
    current_user = await get_current_user(db, token)
    if not current_user:
        return None
    if not current_user.is_active:
        return None
    return current_user

async def get_current_active_superuser(
    db: AsyncSession, token: str
) -> Optional[User]:
    """Get current active superuser"""
    current_user = await get_current_user(db, token)
    if not current_user:
        return None
    if not current_user.is_superuser:
        return None
    return current_user
