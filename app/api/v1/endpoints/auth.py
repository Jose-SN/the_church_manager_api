from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserInDB, UserResponse
from app.services.auth_service import (
    authenticate_user,
    get_current_active_user,
    get_password_hash
)
from app.services.user_service import UserService

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """OAuth2 compatible token login, get an access token for future requests"""
    user = await authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=UserResponse)
async def test_token(current_user: UserInDB = Depends(get_current_active_user)):
    """Test access token"""
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new user"""
    user_service = UserService(db)
    db_user = await user_service.get_by_email(email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user_dict = user_in.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    db_user = await user_service.create(user_dict)
    
    return db_user
