from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext
from pymongo.database import Database
from pydantic import ValidationError
from bson import ObjectId

from app.core.config import settings
from app.models.user import User # TODO: Update this import path
from app.schemas.token import TokenPayload # TODO: Update this import path if necessary
from app.services.user_service import UserService # TODO: Update this import path

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

def authenticate_user(
    db: Database,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: User's password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = db['users'].find_one({'email': email})
    if user and verify_password(password, user['hashed_password']):
        return User(**user)
    return None

def get_current_user(
    db: Database, 
    token: str
) -> Optional[User]:
    """
    Get current user from token
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User object if token is valid, None otherwise
    """
    try:
        token_data = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**token_data)
    except (jwt.JWTError, ValidationError):
        return None
    
    user = db['users'].find_one({'_id': ObjectId(token_data.sub)})
    if user is None:
        return None
    return User(**user)

def get_current_active_user(
    db: Database, 
    token: str
) -> Optional[User]:
    """
    Get current active user
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        Active User object if token is valid and user is active, None otherwise
    """
    current_user = get_current_user(db, token)
    if not current_user:
        return None
    if not current_user.is_active:
        return None
    return current_user

def get_current_active_superuser(
    db: Database, 
    token: str
) -> Optional[User]:
    """
    Get current active superuser
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        Active superuser object if token is valid and user is superuser, None otherwise
    """
    current_user = get_current_user(db, token)
    if not current_user:
        return None
    if not current_user.is_active:
        return None
    if not current_user.is_superuser:
        return None
    return current_user
