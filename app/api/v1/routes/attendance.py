from datetime import datetime, timedelta
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pymongo.database import Database
from bson import ObjectId

from app.schemas.attendance import (
    Attendance,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceStats,
    AttendanceSummary,
    AttendanceSummaryItem,
    BulkAttendanceCreate
)
from app.api.v1.models.user import UserInDB
from app.services.attendance_service import AttendanceService
from app.api.deps import get_db, get_current_active_user
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])

@router.post("/bulk", response_model=List[Attendance], status_code=status.HTTP_201_CREATED)
def bulk_create_attendance(
    bulk_data: BulkAttendanceCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Create multiple attendance records in bulk
    """
    attendance_service = AttendanceService(db)
    
    # Prepare attendance data
    attendance_data_list = []
    for item in bulk_data.items:
        # Only admins can create attendance for other users
        if item.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions to create attendance for user {item.user_id}"
            )
        
        # Check for duplicates
        existing = attendance_service.get_attendance_by_user_and_parent(
            user_id=item.user_id,
            parent_id=bulk_data.parent_id,
            parent_type=bulk_data.parent_type
        )
        
        if existing:
            logger.warning(f"Skipping duplicate attendance for user {item.user_id}")
            continue
        
        # Prepare attendance data
        attendance_data = item.dict()
        attendance_data.update({
            "parent_id": bulk_data.parent_id,
            "parent_type": bulk_data.parent_type,
            "submitted_by": current_user.id,
            "organization_id": bulk_data.organization_id
        })
        attendance_data_list.append(attendance_data)
    
    if not attendance_data_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid attendance records to create"
        )
    
    try:
        # Use bulk create with transaction
        result = attendance_service.bulk_create_attendance(attendance_data_list)
        return result
    except Exception as e:
        logger.error(f"Error in bulk attendance creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating attendance records: {str(e)}"
        )

@router.post("", response_model=Attendance, status_code=status.HTTP_201_CREATED)
def create_attendance(
    attendance_in: AttendanceCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Create a new attendance record
    """
    attendance_service = AttendanceService(db)
    
    # Check if attendance record already exists
    existing = attendance_service.get_attendance_by_user_and_parent(
        user_id=attendance_in.user_id,
        parent_id=attendance_in.parent_id,
        parent_type=attendance_in.parent_type
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance record already exists for this user and parent"
        )
    
    # Prepare attendance data
    attendance_data = attendance_in.dict()
    attendance_data["submitted_by"] = current_user.id
    
    try:
        return attendance_service.create(attendance_data)
    except Exception as e:
        logger.error(f"Error creating attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=List[Attendance])
def list_attendance(
    user_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    parent_type: Optional[str] = None,
    status: Optional[str] = None,
    question_id: Optional[str] = None,
    submitted_by: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    List attendance records with filtering options
    """
    attendance_service = AttendanceService(db)
    
    # Regular users can only see their own attendance
    if user_id and user_id != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view other users' attendance"
        )
    
    # If no user_id is provided and user is not admin, only show their records
    if not user_id and not current_user.is_superuser:
        user_id = str(current_user.id)
    
    # Validate parent_type if provided
    if parent_type and parent_type not in ['event', 'meeting']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parent_type. Must be 'event' or 'meeting'"
        )
    
    # Validate status if provided
    if status and status not in [s.value for s in AttendanceStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be one of: present, absent, late, excused"
        )
    
    # Prepare filters
    filters = {}
    if user_id:
        filters["user_id"] = user_id
    if parent_id:
        filters["parent_id"] = parent_id
    if parent_type:
        filters["parent_type"] = parent_type
    if status:
        filters["status"] = status
    if question_id:
        filters["question_id"] = question_id
    if submitted_by:
        filters["submitted_by"] = submitted_by
    if start_date:
        filters["created_at"] = {"$gte": start_date}
    if end_date:
        filters["created_at"] = {"$lte": end_date}
    
    try:
        return attendance_service.get_multi(
            skip=skip,
            limit=limit,
            filters=filters
        )
    except Exception as e:
        logger.error(f"Error listing attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{attendance_id}", response_model=Attendance)
def get_attendance(
    attendance_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Get a specific attendance record
    """
    attendance_service = AttendanceService(db)
    attendance = attendance_service.get_attendance_by_id(attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only admins or the user who submitted the attendance can view it
    if attendance.submitted_by != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return attendance

@router.get("/user/{user_id}", response_model=List[Attendance])
def get_attendance_for_user(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
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
    return attendance_service.get_attendance(
        user_id=user_id,
        skip=skip,
        limit=limit
    )

@router.put("/{attendance_id}", response_model=Attendance)
def update_attendance(
    attendance_id: str,
    attendance_in: AttendanceUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Update an attendance record
    """
    attendance_service = AttendanceService(db)
    attendance = attendance_service.get_attendance_by_id(attendance_id)
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only admins or the user who submitted the attendance can update it
    if attendance.submitted_by != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        return attendance_service.update_attendance(attendance_id, attendance_in)
        
        return await attendance_service.update(attendance_id, update_data)
    except Exception as e:
        logger.error(f"Error updating attendance {attendance_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    attendance_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> None:
    """
    Delete an attendance record
    """
    attendance_service = AttendanceService(db)
    
    # Get the existing attendance record
    attendance = attendance_service.get_attendance_by_id(attendance_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )
    
    # Only admins or the user who submitted the attendance can delete it
    if attendance.submitted_by != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        attendance_service.delete_attendance(attendance_id)
    except Exception as e:
        logger.error(f"Error deleting attendance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return None

@router.get("/stats", response_model=AttendanceStats)
def get_attendance_stats(
    parent_id: Optional[str] = None,
    parent_type: Optional[str] = None,
    user_id: Optional[str] = None,  # Changed to str for ObjectId
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    question_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)  # Changed to pymongo Database
) -> Any:
    """
    Get attendance statistics with optional filters
    """
    # Regular users can only see their own stats unless they're admins
    if user_id and user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view other users' statistics"
        )
    
    # If no user_id is provided and user is not admin, only show their stats
    if not user_id and not current_user.is_superuser:
        user_id = str(current_user.id) # Ensure user_id is string for comparison
    
    # Validate parent_type if provided
    if parent_type and parent_type not in ['event', 'meeting']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_type must be either 'event' or 'meeting'"
        )
    
    attendance_service = AttendanceService(db)
    
    try:
        return attendance_service.get_attendance_stats(
            parent_id=parent_id,
            parent_type=parent_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            question_id=question_id
        )
    except Exception as e:
        logger.error(f"Error getting attendance stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/summary", response_model=List[AttendanceSummaryItem])
def get_attendance_summary(
    organization_id: str,  # Changed to str for ObjectId
    start_date: datetime,
    end_date: datetime,
    period: str = Query("daily", enum=["daily", "weekly", "monthly"]),
    parent_type: Optional[str] = None,
    user_id: Optional[str] = None,  # Changed to str for ObjectId
    question_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)  # Changed to pymongo Database
) -> Any:
    """
    Get attendance summary aggregated by period (daily, weekly, or monthly)
    
    Args:
        organization_id: ID of the organization
        start_date: Start date for the summary
        end_date: End date for the summary
        period: Time period for grouping ('daily', 'weekly', 'monthly')
        parent_type: Optional filter by parent type ('event' or 'meeting')
        user_id: Optional filter by user ID
        question_id: Optional filter by question ID
        
    Returns:
        List of attendance summary items
    """
    # Regular users can only see their own summaries unless they're admins
    if user_id and user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view other users' summaries"
        )
    
    # If no user_id is provided and user is not admin, only show their summaries
    if not user_id and not current_user.is_superuser:
        user_id = str(current_user.id) # Ensure user_id is string
    
    # Validate parent_type if provided
    if parent_type and parent_type not in ['event', 'meeting']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_type must be either 'event' or 'meeting'"
        )
    
    attendance_service = AttendanceService(db)
    
    try:
        return attendance_service.get_attendance_summary(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            period=period,
            parent_type=parent_type,
            user_id=user_id,
            question_id=question_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting attendance summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the attendance summary"
        )

@router.get("/not-attended/{parent_type}/{parent_id}", response_model=List[str])  # Changed response_model to List[str]
def get_not_attended_users(
    parent_id: str,
    parent_type: str,
    user_ids: List[str] = Query([], description="List of user IDs to check"),  # Changed to List[str]
    status: str = "absent",
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)  # Changed to pymongo Database
) -> Any:
    """
    Get list of user IDs who did not attend a specific event/meeting
    
    Args:
        parent_id: ID of the parent (event or meeting)
        parent_type: Type of the parent ('event' or 'meeting')
        user_ids: List of user IDs to check (if empty, checks all users)
        status: Status to check for (default: 'absent')
        
    Returns:
        List of user IDs who did not attend
    """
    # Validate parent_type
    if parent_type not in ['event', 'meeting']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="parent_type must be either 'event' or 'meeting'"
        )
    
    # If user_ids is empty and user is not admin, only check their own attendance
    if not user_ids and not current_user.is_superuser:
        user_ids = [str(current_user.id)]  # Ensure user_id is string
    
    attendance_service = AttendanceService(db)
    
    try:
        return attendance_service.get_non_attended_users(
            parent_id=parent_id,
            parent_type=parent_type,
            user_ids=user_ids
        )
    except Exception as e:
        logger.error(f"Error getting not attended users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
