from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic_settings import BaseSettings

class AttendanceStatus(str):
    PRESENT = 'present'
    ABSENT = 'absent'
    LATE = 'late'
    EXCUSED = 'excused'


class AttendanceBase(BaseModel):
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
