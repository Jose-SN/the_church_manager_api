from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.models.user import User as UserModel
from app.api.v1.schemas.attendance import (
    Attendance,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceStats,
    AttendanceSummary,
)
from app.services.attendance_service import AttendanceService
from app.api.deps import get_current_active_user, get_current_active_superuser

router = APIRouter()

@router.post(
    "/", 
    response_model=Attendance, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new attendance record",
    description="Create a new attendance record. Regular users can only create records for themselves.",
    response_description="The created attendance record"
)
async def create_attendance(
    attendance_in: AttendanceCreate,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Attendance:
    """
    Create a new attendance record.
    """
    service = AttendanceService(db)
    
    # Check if attendance record already exists
    existing = await service.get_attendance_by_user_and_event(
        user_id=attendance_in.user_id,
        event_id=attendance_in.event_id,
        meeting_id=attendance_in.meeting_id
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists for this user and event/meeting"
        )
    
    # Only admins can create attendance for other users
    if attendance_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create attendance for another user"
        )
    
    # Set recorded_by to current user
    attendance_data = attendance_in.dict()
    attendance_data["recorded_by"] = current_user.id
    
    return await service.create(attendance_data)

@router.get(
    "/{attendance_id}", 
    response_model=Attendance,
    summary="Get an attendance record by ID",
    description="Retrieve a specific attendance record by its ID. Users can only access their own records unless they are admins.",
    response_description="The requested attendance record"
)
async def get_attendance(
    attendance_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Attendance:
    """
    Get a specific attendance record by ID.
    """
    service = AttendanceService(db)
    attendance = await service.get_attendance_by_id(attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only admins or the user themselves can view the record
    if attendance.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view this attendance record"
        )
    
    return attendance

@router.get(
    "/", 
    response_model=List[Attendance],
    summary="List attendance records",
    description="List attendance records with optional filtering. Regular users can only see their own records.",
    response_description="A list of attendance records"
)
async def list_attendance(
    user_id: Optional[int] = None,
    event_id: Optional[int] = None,
    meeting_id: Optional[int] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Attendance]:
    """
    List attendance records with optional filtering.
    Regular users can only see their own records unless they are admins.
    """
    service = AttendanceService(db)
    
    # Non-admins can only see their own records
    if not current_user.is_superuser:
        user_id = current_user.id
    
    return await service.list_attendance(
        user_id=user_id,
        event_id=event_id,
        meeting_id=meeting_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.put(
    "/{attendance_id}", 
    response_model=Attendance,
    summary="Update an attendance record",
    description="Update an existing attendance record. Users can only update their own records unless they are admins.",
    response_description="The updated attendance record"
)
async def update_attendance(
    attendance_id: int,
    attendance_in: AttendanceUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Attendance:
    """
    Update an attendance record.
    """
    service = AttendanceService(db)
    
    # Get the existing attendance
    attendance = await service.get_attendance_by_id(attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Check permissions
    if attendance.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this attendance record"
        )
    
    # Update the record
    updated_attendance = await service.update(
        attendance_id=attendance_id,
        attendance_data=attendance_in.dict(exclude_unset=True)
    )
    
    if not updated_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    return updated_attendance

@router.delete(
    "/{attendance_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an attendance record",
    description="Delete an attendance record. Only admins or the user who created the record can delete it.",
    response_description="No content"
)
async def delete_attendance(
    attendance_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an attendance record.
    """
    service = AttendanceService(db)
    
    # Get the existing attendance
    attendance = await service.get_attendance_by_id(attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only admins or the user who created the record can delete it
    if attendance.recorded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this attendance record"
        )
    
    success = await service.delete(attendance_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    return None

@router.get(
    "/event/{event_id}/stats", 
    response_model=AttendanceStats,
    summary="Get attendance statistics for an event",
    description="Retrieve statistics for a specific event, including counts by status.",
    response_description="Attendance statistics for the event"
)
async def get_event_attendance_stats(
    event_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AttendanceStats:
    """
    Get attendance statistics for a specific event.
    """
    service = AttendanceService(db)
    return await service.get_attendance_stats(event_id=event_id)

@router.get(
    "/summary/", 
    response_model=List[AttendanceSummary],
    summary="Get attendance summary by period",
    description="Get attendance summary aggregated by period (daily, weekly, or monthly). Only accessible by superusers.",
    response_description="A list of attendance summaries by period"
)
async def get_attendance_summary(
    organization_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: UserModel = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
) -> List[AttendanceSummary]:
    """
    Get attendance summary by period (daily, weekly, or monthly).
    Only accessible by superusers.
    """
    service = AttendanceService(db)
    return await service.get_attendance_summary(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        period=period
    )

@router.get(
    "/event/{event_id}/not-attended/", 
    response_model=List[dict],
    summary="Get users who did not attend an event",
    description="Retrieve a list of users who did not attend a specific event or had a specific status.",
    response_description="List of users who did not attend the event"
)
async def get_not_attended_users(
    event_id: int,
    status: str = Query("absent", regex="^(absent|present|late|excused)$"),
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Get users who did not attend a specific event (or had specific status).
    """
    service = AttendanceService(db)
    users = await service.get_not_attended_users(event_id, status)
    
    # Convert to dict and exclude sensitive data
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active
        }
        for user in users
    ]

@router.post(
    "/bulk/", 
    response_model=List[Attendance], 
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create attendance records",
    description="Create multiple attendance records at once. Only accessible by admins.",
    response_description="List of created attendance records"
)
async def bulk_create_attendance(
    attendance_list: List[AttendanceCreate],
    current_user: UserModel = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Attendance]:
    """
    Create multiple attendance records at once.
    Only accessible by admins.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform bulk operations"
        )
    
    service = AttendanceService(db)
    
    # Convert Pydantic models to dicts and add recorded_by
    attendance_data = [
        {**attendance.dict(), "recorded_by": current_user.id}
        for attendance in attendance_list
    ]
    
    return await service.bulk_create_attendance(attendance_data)
