from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_active_user
from app.schemas.meeting import MeetingCreate, MeetingInDB, MeetingUpdate, MeetingAttendeeStatus
from app.api.v1.services.meeting_service import MeetingService

router = APIRouter()

@router.post("/", response_model=MeetingInDB, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_in: MeetingCreate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Create a new meeting
    """
    meeting_service = MeetingService()
    return await meeting_service.create_meeting(
        meeting_in=meeting_in,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/{meeting_id}", response_model=MeetingInDB)
async def get_meeting(
    meeting_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get a meeting by ID with attendee status
    """
    meeting_service = MeetingService()
    meeting = await meeting_service.get_meeting_with_attendees(meeting_id)
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check organization access
    if str(meeting.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this meeting"
        )
    
    return meeting

@router.get("/", response_model=List[MeetingInDB])
async def list_meetings(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    List meetings with optional date filtering
    """
    meeting_service = MeetingService()
    return await meeting_service.list_meetings(
        organization_id=current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )

@router.put("/{meeting_id}", response_model=MeetingInDB)
async def update_meeting(
    meeting_id: str,
    meeting_in: MeetingUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Update a meeting
    """
    meeting_service = MeetingService()
    meeting = await meeting_service.get_meeting(meeting_id)
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Check organization access and creator
    if (str(meeting.organization_id) != str(current_user.organization_id) or 
        str(meeting.created_by) != str(current_user.id)) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this meeting"
        )
    
    return await meeting_service.update_meeting(meeting_id, meeting_in)

@router.post("/{meeting_id}/attendees/{user_id}", response_model=dict)
async def update_attendance_status(
    meeting_id: str,
    user_id: str,
    status: MeetingAttendeeStatus,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Update attendance status for a meeting
    """
    # Users can only update their own status unless they're an admin
    if str(user_id) != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own attendance status"
        )
    
    meeting_service = MeetingService()
    return await meeting_service.update_attendance(
        meeting_id=meeting_id,
        user_id=user_id,
        status=status
    )

@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> None:
    """
    Delete a meeting
    """
    meeting_service = MeetingService()
    meeting = await meeting_service.get_meeting(meeting_id)
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Only meeting creator or admin can delete
    if (str(meeting.created_by) != str(current_user.id) and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this meeting"
        )
    
    await meeting_service.delete_meeting(meeting_id)
