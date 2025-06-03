from datetime import timedelta, datetime
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    get_current_active_user, 
    get_current_active_admin,
    get_password_hash,
    verify_password
)
from app.api.v1.models.user import UserCreate, UserUpdate, UserInDB, UserRole, UserRegister
from app.api.v1.services.user_service import UserService
from app.services.email_service import send_otp_email, send_password_reset_confirmation
from app.api.deps import get_db

# Pydantic models for request/response schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    new_password_confirm: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

router = APIRouter(prefix="", tags=["Users & Authentication"])

@router.post("/auth/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user_service = UserService(db)
    
    # Authenticate user
    user = await user_service.authenticate(
        email=form_data.username, 
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Prepare user data for token
    user_data = {
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser
    }
    
    return {
        "access_token": create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            user_data=user_data
        ),
        "refresh_token": create_refresh_token(
            subject=str(user.id),
            expires_delta=refresh_token_expires
        ),
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "profile_image_url": user.profile_image_url
        }
    }

@router.post("/auth/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    user_service = UserService(db)
    
    # Check if user with this email already exists
    existing_user = await user_service.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists"
        )
    
    # Create user with default role (non-admin, inactive by default)
    user_data = user_in.dict(exclude={"password"})
    user_data.update({
        "hashed_password": get_password_hash(user_in.password),
        "is_active": settings.USERS_OPEN_REGISTRATION,  # Auto-activate if open registration is enabled
        "is_superuser": False
    })
    
    user = await user_service.create(user_data)
    return user

@router.post("/auth/refresh-token", response_model=dict)
async def refresh_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    # Implementation of token refresh would go here
    # This is a placeholder - you would need to implement token validation
    # and refresh logic based on your security requirements
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not implemented yet"
    )

@router.get("/me", response_model=UserInDB)
async def read_user_me(
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get current user
    """
    return current_user

@router.patch("/me", response_model=UserInDB)
async def update_user_me(
    *,
    user_in: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update own user
    """
    user_service = UserService(db)
    user = await user_service.update(
        user_id=current_user.id,
        user_in=user_in,
        current_user=current_user
    )
    return user

@router.post("", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    user_in: UserCreate,
    current_user: UserInDB = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create new user
    """
    user_service = UserService(db)
    
    # Check if user with this email already exists
    user = await user_service.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    # Only superusers can create admin users
    if user_in.role == UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create admin user",
        )
    
    user = await user_service.create(user_in=user_in)
    return user

@router.get("", response_model=List[UserInDB])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Retrieve users
    """
    user_service = UserService(db)
    if current_user.is_superuser:
        users = await user_service.get_multi(skip=skip, limit=limit)
    else:
        # Regular users can only see active users
        users = await user_service.get_multi(
            skip=skip, 
            limit=limit,
            filters={"is_active": True}
        )
    return users

@router.get("/{user_id}", response_model=UserInDB)
async def read_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific user by id
    """
    user_service = UserService(db)
    user = await user_service.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Regular users can only see their own profile or active users
    if not current_user.is_superuser and user_id != current_user.id and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user

@router.put("/{user_id}", response_model=UserInDB)
async def update_user(
    *,
    user_id: int,
    user_in: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update a user
    """
    user_service = UserService(db)
    
    # Check if user exists
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow users to update their own account or admin users
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Only superusers can change roles or superuser status
    if (user_in.role is not None or user_in.is_superuser is not None) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to change user role or status"
        )
    
    # Prevent removing the last superuser status
    if user_in.is_superuser is False and user.is_superuser:
        total_superusers = await user_service.count_superusers()
        if total_superusers <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last superuser"
            )
    
    updated_user = await user_service.update(user_id, user_in)
    return updated_user

@router.delete("/{user_id}", response_model=UserInDB)
async def delete_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete a user
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService(db)
    user = await user_service.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting own account
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Prevent deleting the last superuser
    if user.is_superuser:
        total_superusers = await user_service.count_superusers()
        if total_superusers <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last superuser"
            )
    
    await user_service.remove(user_id)
    return user

@router.get("/not-attended/{event_id}", response_model=List[UserInDB])
async def get_users_not_attended_event(
    event_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get users who did not attend a specific event
    """
    user_service = UserService(db)
    try:
        users = await user_service.get_users_not_attended_event(event_id=event_id)
        return users
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/auth/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Initiate password reset by sending OTP to user's email
    """
    user_service = UserService(db)
    result = await user_service.initiate_password_reset(request.email)
    
    if not result:
        # Don't reveal that user doesn't exist
        return {"message": "If an account exists with this email, you will receive an OTP"}
    
    user_id, otp = result
    
    # Send OTP via email in background
    background_tasks.add_task(
        send_otp_email,
        email=request.email,
        otp=otp
    )
    
    # In production, you might want to return a user_id or token instead of the OTP
    return {
        "message": "OTP sent to your email",
        "user_id": user_id  # This would be used in the reset-password endpoint
    }

@router.post("/auth/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Reset password using OTP
    """
    # Validate password confirmation
    if request.new_password != request.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    user_service = UserService(db)
    
    # Get user by email to get the user_id
    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Reset password using OTP
    success = await user_service.reset_password_with_otp(
        user_id=str(user.id),
        otp=request.otp,
        new_password=request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Send confirmation email in background
    background_tasks.add_task(
        send_password_reset_confirmation,
        email=request.email
    )
    
    return {"message": "Password has been reset successfully"}

@router.post("/auth/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Change password for authenticated users
    """
    # Validate password confirmation
    if request.new_password != request.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    user_service = UserService(db)
    
    try:
        success = await user_service.update_password(
            user_id=str(current_user.id),
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
            
        return {"message": "Password updated successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )