from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Literal
from bson import ObjectId
from pydantic_settings import BaseSettings

# Define the allowed status values as a type
AttendanceStatus = Literal['present', 'absent', 'late', 'excused']

class AttendanceBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    userId: str = Field(..., min_length=1)
    eventId: Optional[str] = None
    meetingId: Optional[str] = None
    date: datetime
    status: AttendanceStatus
    notes: Optional[str] = None
    organizationId: str
    type: str  # event or meeting

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    userId: Optional[str] = None
    eventId: Optional[str] = None
    meetingId: Optional[str] = None
    date: Optional[datetime] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None
    organizationId: Optional[str] = None
    type: Optional[str] = None

class AttendanceInDB(AttendanceBase):
    id: str
    created_at: datetime
    updated_at: datetime

class AttendanceStats(BaseModel):
    total: int
    present: int
    absent: int
    late: int
    percentage: float

class AttendanceSummary(BaseModel):
    date: datetime
    total: int
    present: int
    absent: int
    late: int
    percentage: float
