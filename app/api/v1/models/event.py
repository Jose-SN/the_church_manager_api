from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel, Field

from app.models.user import User
from app.models.attendance import Attendance

class Event(BaseModel):
    id: Optional[ObjectId] = Field(alias='_id', default=None)
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_active: bool = True
    ended: bool = False
    created_by: str  # ObjectId of the creator
    creator: Optional[User] = None
    attendees: List[Attendance] = []
    created_at: datetime = datetime.utcnow()
    modification_date: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
