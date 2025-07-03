from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.api.v1.models.user import User as UserModel
from app.api.v1.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve users"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    user_service = UserService(db)
    users = await user_service.get_multi(skip=skip, limit=limit)
    return users

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    user_in: UserCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new user"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    user_service = UserService(db)
    db_user = await user_service.get_by_email(email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = await user_service.create(user_in)
    return user

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get current user"""
    return current_user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user"""
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    user_service = UserService(db)
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user"""
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    user_service = UserService(db)
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user = await user_service.update(user, user_in)
    return user
