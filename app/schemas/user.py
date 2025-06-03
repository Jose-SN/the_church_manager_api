from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.role import Role as RoleSchema

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """Schema for updating user data"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    """Base schema for user data in database"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class User(UserInDBBase):
    """Schema for user data returned to clients"""
    roles: List[RoleSchema] = []

class UserInDB(UserInDBBase):
    """Schema for user data in database (includes hashed password)"""
    hashed_password: str

# Token schemas
class Token(BaseModel):
    """Schema for JWT token"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for token data"""
    email: Optional[str] = None
    scopes: List[str] = []

# Request/Response schemas
class UserCreateRequest(UserCreate):
    """Schema for user creation request"""
    pass

class UserResponse(User):
    """Schema for user response"""
    pass

class UserUpdateRequest(UserUpdate):
    """Schema for user update request"""
    pass

class UserListResponse(BaseModel):
    """Schema for listing users"""
    items: List[User]
    total: int
