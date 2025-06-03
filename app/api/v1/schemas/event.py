from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.pyobjectid import PyObjectId

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
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_by: Optional[PyObjectId] = Field(None, description="User ID of the event creator") # Assuming created_by can be optional or system-generated
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modification_date: Optional[datetime] = None

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True # Allows using alias '_id' during initialization
        arbitrary_types_allowed = True # Necessary for PyObjectId

class Event(EventInDBBase):
    # Inherits fields from EventInDBBase and EventBase
    # Add any additional fields specific to the Event response model here, if any
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
