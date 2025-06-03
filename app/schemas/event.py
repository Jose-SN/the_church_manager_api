from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class EventBase(BaseModel):
    title: str = Field(..., description="Title of the event")
    description: Optional[str] = None
    start_time: datetime = Field(..., description="Start time of the event")
    end_time: Optional[datetime] = Field(None, description="End time of the event")
    location: Optional[str] = None
    is_active: bool = Field(True, description="Whether the event is active")
    ended: bool = Field(False, description="Whether the event has ended")

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    ended: Optional[bool] = None

class EventInDBBase(EventBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Event(EventInDBBase):
    pass

class EventFilter(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    ended: Optional[bool] = None
    start_time_after: Optional[datetime] = None
    start_time_before: Optional[datetime] = None

class EventEnd(BaseModel):
    end_time: Optional[datetime] = None
