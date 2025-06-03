from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum

class StatusType(str, Enum):
    COURSE = 'Course'
    CHAPTER = 'Chapter'
    FILE = 'File'

class StatusBase(BaseModel):
    """Base schema for status records."""
    parent_id: str = Field(..., description="ID of the parent object (Course, Chapter, or File)")
    parent_type: StatusType = Field(..., description="Type of the parent object")
    percentage: Optional[str] = Field(None, description="Completion percentage")
    comment: Optional[str] = Field(None, description="Optional comment")
    rating: Optional[float] = Field(None, description="Rating value")
    reward: Optional[float] = Field(None, description="Reward value")
    created_by: int = Field(..., description="ID of the user who created this status")

class StatusCreate(StatusBase):
    """Schema for creating a new status."""
    pass

class StatusUpdate(StatusBase):
    """Schema for updating a status."""
    pass

class Status(StatusBase):
    """Schema for a status record."""
    id: int
    creation_date: datetime
    modification_date: datetime

    class Config:
        from_attributes = True

class StatusOverview(BaseModel):
    """Schema for status overview."""
    total_count: int
    by_type: dict
    by_date: dict
    recent_updates: List[Status]
    average_ratings: dict
