from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic_settings import BaseSettings

class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    startDate: datetime
    endDate: datetime
    location: str
    type: str
    organizationId: str
    attendees: List[str] = []
    image: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None

class MeetingCreate(MeetingBase):
    pass

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    location: Optional[str] = None
    type: Optional[str] = None
    organizationId: Optional[str] = None
    attendees: Optional[List[str]] = None
    image: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MeetingInDB(MeetingBase):
    id: str
    created_at: datetime
    updated_at: datetime

class MeetingAttendee(BaseModel):
    userId: str
    firstName: str
    lastName: str
    email: str
    status: str
    notes: Optional[str] = None

class MeetingAttendance(BaseModel):
    meetingId: str
    userId: str
    date: datetime
    status: str
    notes: Optional[str] = None
