from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.models.user import TokenData, UserInDB
from app.api.v1.services.user_service import UserService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token"
)

# JWT token creation and validation functions
def create_access_token(
    subject: str, 
    expires_delta: Optional[timedelta] = None,
    user_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    if user_data:
        to_encode.update(user_data)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """
    Get the current authenticated user from the JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    user = await UserService().get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """
    Get the current active user (checks if user is active)
    """
    if not current_user.approved:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_admin(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Get the current active admin user
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

# Password hashing and verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    import bcrypt
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    import bcrypt
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')