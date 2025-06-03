from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field, validator, HttpUrl

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

# Shared properties
class AttendanceBase(BaseModel):
    """
    Base schema for attendance records.
    Uses parent_id and parent_type pattern to support both events and meetings.
    """
    user_id: int = Field(..., description="ID of the user this attendance is for")
    parent_id: str = Field(..., description="ID of the parent object (event or meeting)")
    parent_type: str = Field(..., description="Type of the parent object ('event' or 'meeting')")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, description="Optional notes about the attendance")
    question_id: Optional[str] = Field(None, description="ID of a related question if applicable")
    submitted_by: int = Field(..., description="ID of the user who recorded this attendance")

    @validator('parent_type')
    def validate_parent_type(cls, v):
        if v not in ['event', 'meeting']:
            raise ValueError("parent_type must be either 'event' or 'meeting'")
        return v

    class Config:
        orm_mode = True
        use_enum_values = True

# Properties to receive via API on creation
class AttendanceCreate(AttendanceBase):
    """Schema for creating a new attendance record"""
    pass

# Properties to receive via API on update
class AttendanceUpdate(BaseModel):
    """Schema for updating an existing attendance record"""
    status: Optional[AttendanceStatus] = Field(None, description="Updated attendance status")
    notes: Optional[str] = Field(None, description="Updated notes")
    question_id: Optional[str] = Field(None, description="Updated question ID")

# Properties shared by models stored in DB
class AttendanceInDBBase(AttendanceBase):
    """Base schema for attendance records in the database"""
    id: int
    created_at: datetime
    modification_date: Optional[datetime] = None

    class Config:
        orm_mode = True

# Properties to return to client
class Attendance(AttendanceInDBBase):
    """Schema for returning attendance records to the client"""
    pass

# Properties stored in DB
class AttendanceInDB(AttendanceInDBBase):
    """Schema for attendance records in the database"""
    pass

# Statistics
class AttendanceStats(BaseModel):
    """Schema for attendance statistics"""
    total: int = Field(..., description="Total number of attendance records")
    present: int = Field(..., description="Number of 'present' records")
    absent: int = Field(..., description="Number of 'absent' records")
    late: int = Field(..., description="Number of 'late' records")
    excused: int = Field(..., description="Number of 'excused' records")
    percentage: float = Field(..., description="Attendance percentage (0-100)")

# Summary item
class AttendanceSummaryItem(BaseModel):
    """Schema for a single attendance summary item"""
    period: str = Field(..., description="Time period identifier (daily, weekly, monthly)")
    date: str = Field(..., description="ISO format date of the period")
    total: int = Field(..., description="Total number of attendance records in this period")
    present: int = Field(..., description="Number of 'present' records in this period")
    absent: int = Field(..., description="Number of 'absent' records in this period")
    late: int = Field(..., description="Number of 'late' records in this period")
    excused: int = Field(..., description="Number of 'excused' records in this period")
    percentage: float = Field(..., description="Attendance percentage for this period (0-100)")

# Summary response
class AttendanceSummary(BaseModel):
    """Schema for the attendance summary response"""
    items: List[AttendanceSummaryItem] = Field(..., description="List of summary items")
    total: AttendanceStats = Field(..., description="Overall statistics across all periods")

# Bulk creation
class BulkAttendanceItem(BaseModel):
    """Schema for a single attendance record in a bulk create operation"""
    user_id: int = Field(..., description="ID of the user this attendance is for")
    status: AttendanceStatus = Field(..., description="Attendance status")
    notes: Optional[str] = Field(None, description="Optional notes about the attendance")
    question_id: Optional[str] = Field(None, description="ID of a related question if applicable")

class BulkAttendanceCreate(BaseModel):
    """Schema for bulk attendance creation"""
    items: List[BulkAttendanceItem] = Field(..., description="List of attendance records to create")
    parent_id: str = Field(..., description="ID of the parent object (event or meeting)")
    parent_type: str = Field(..., description="Type of the parent object ('event' or 'meeting')")
    organization_id: int = Field(..., description="ID of the organization")

    @validator('parent_type')
    def validate_parent_type(cls, v):
        if v not in ['event', 'meeting']:
            raise ValueError("parent_type must be either 'event' or 'meeting'")
        return v
