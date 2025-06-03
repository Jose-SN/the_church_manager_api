from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum
from bson import ObjectId
from pydantic_settings import BaseSettings


class Role(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: Optional[ObjectId] = Field(default=None, alias='_id')
    name: str
    description: Optional[str] = None
    permissions: List[ObjectId] = Field(default_factory=list) # Assuming permissions are ObjectIds of Permission documents

class Permission(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    id: Optional[ObjectId] = Field(default=None, alias='_id')
    name: str
    description: Optional[str] = None
    # roles: List[ObjectId] = Field(default_factory=list) # If Permission tracks roles, uncomment and use ObjectId


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, (str, ObjectId)):
            raise ValueError("Not a valid ObjectId")
        return str(v)

class UserBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
    email: EmailStr
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    roles: List[ObjectId] = Field(default_factory=list)
    is_superuser: bool = Field(default=False)
    approved: bool = False
    is_active: bool = True
    profileImage: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    dateOfBirth: Optional[str] = None
    primaryUser: Optional[bool] = False
    associatedUsers: Optional[List[ObjectIdStr]] = []
    otp: Optional[str] = None
    otp_expires: Optional[datetime] = None
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    passwordConfirm: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    profileImage: Optional[str] = None
    relationship: Optional[str] = None
    dateOfBirth: Optional[str] = None
    primaryUser: Optional[bool] = None
    associatedUsers: Optional[List[ObjectIdStr]] = None

class UserInDB(UserBase):
    id: ObjectIdStr
    hashed_password: str
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserInDB

class TokenData(BaseModel):
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None
    approved: Optional[bool] = None

# Initialize BaseSettings to ensure environment variables are loaded
_ = BaseSettings()