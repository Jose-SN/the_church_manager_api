from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.attendance import (
    Attendance,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceStats,
    AttendanceSummary
)
from app.models.user import UserInDB
from app.api.v1.services.attendance_service import AttendanceService
from app.api.deps import get_db, get_current_active_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("", response_model=Attendance, status_code=status.HTTP_201_CREATED)
async def create_attendance(
    attendance_in: AttendanceCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new attendance record
    """
    attendance_service = AttendanceService(db)
    
    # Check if attendance record already exists
    existing = await attendance_service.get_attendance_by_user_and_event(
        user_id=attendance_in.user_id,
        event_id=attendance_in.event_id,
        meeting_id=attendance_in.meeting_id
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists"
        )
    
    # Only admins can create attendance for other users
    if attendance_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    attendance_data = attendance_in.dict()
    attendance_data["recorded_by"] = current_user.id
    
    return await attendance_service.create(attendance_data)

@router.get("", response_model=List[Attendance])
async def get_attendance(
    user_id: Optional[str] = None,
    event_id: Optional[str] = None,
    meeting_id: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Attendance]:
    """
    Get attendance records with filtering options
    """
    attendance_service = AttendanceService(db)
    
    # Regular users can only see their own attendance
    if user_id and user_id != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # If no user_id is provided and user is not admin, only show their records
    if not user_id and not current_user.is_superuser:
        user_id = str(current_user.id)
    
    return await attendance_service.get_attendance(
        user_id=user_id,
        event_id=event_id,
        meeting_id=meeting_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.get("/event/{event_id}", response_model=List[Attendance])
async def get_attendance_for_event(
    event_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Attendance]:
    """
    Get attendance records for a specific event
    """
    attendance_service = AttendanceService(db)
    return await attendance_service.get_attendance(
        event_id=event_id,
        skip=skip,
        limit=limit
    )

@router.get("/user/{user_id}", response_model=List[Attendance])
async def get_attendance_for_user(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Attendance]:
    """
    Get attendance records for a specific user
    """
    # Users can only see their own attendance unless they're admin
    if user_id != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    attendance_service = AttendanceService(db)
    return await attendance_service.get_attendance(
        user_id=user_id,
        skip=skip,
        limit=limit
    )

@router.put("/{attendance_id}", response_model=Attendance)
async def update_attendance(
    attendance_id: str,
    attendance_in: AttendanceUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Attendance:
    """
    Update an attendance record
    """
    attendance_service = AttendanceService(db)
    attendance = await attendance_service.get_attendance_by_id(attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only allow updates by admins or the user who created the record
    if attendance.recorded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await attendance_service.update(
        attendance_id=attendance_id,
        attendance_update=attendance_in
    )

@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an attendance record
    """
    attendance_service = AttendanceService(db)
    attendance = await attendance_service.get_attendance_by_id(attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only allow deletes by admins or the user who created the record
    if attendance.recorded_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await attendance_service.delete(attendance_id=attendance_id)
    return None

@router.get("/stats/event/{event_id}", response_model=AttendanceStats)
async def get_event_attendance_stats(
    event_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> AttendanceStats:
    """
    Get attendance statistics for an event
    """
    attendance_service = AttendanceService(db)
    return await attendance_service.get_attendance_stats(event_id=event_id)

@router.get("/stats/summary", response_model=List[AttendanceSummary])
async def get_attendance_summary(
    organization_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    period: str = Query("daily", enum=["daily", "weekly", "monthly"]),
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[AttendanceSummary]:
    """
    Get attendance summary by period (daily, weekly, or monthly)
    """
    attendance_service = AttendanceService(db)
    return await attendance_service.get_attendance_summary(
        organization_id=organization_id,
        start_date=start_date,
        end_date=end_date,
        period=period
    )

@router.get("/not-attended/event/{event_id}", response_model=List[UserInDB])
async def get_not_attended_users(
    event_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[UserInDB]:
    """
    Get users who did not attend a specific event
    """
    attendance_service = AttendanceService(db)
    return await attendance_service.get_not_attended_users(event_id=event_id)
