from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic_settings import BaseSettings

class GuestBase(BaseModel):
    firstName: str = Field(..., min_length=1)
    lastName: str = Field(..., min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organizationId: Optional[str] = None
    dateOfBirth: Optional[str] = None
    relationship: Optional[str] = None
    primaryUser: Optional[bool] = False
    associatedUsers: Optional[List[str]] = []
    profileImage: Optional[str] = None
    approved: bool = False

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    organizationId: Optional[str] = None
    dateOfBirth: Optional[str] = None
    relationship: Optional[str] = None
    primaryUser: Optional[bool] = None
    associatedUsers: Optional[List[str]] = None
    profileImage: Optional[str] = None
    approved: Optional[bool] = None

class GuestInDB(GuestBase):
    id: str
    created_at: datetime
    updated_at: datetime

class GuestAttendance(BaseModel):
    eventId: str
    meetingId: Optional[str] = None
    date: datetime
    status: str
    notes: Optional[str] = None
