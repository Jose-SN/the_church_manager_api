from datetime import datetime
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database
from bson import ObjectId

from app.schemas.event import Event, EventCreate, EventUpdate, EventFilter, EventEnd
from app.services.event_service import EventService
from app.api.deps import get_db, get_current_active_user
from app.models.user import UserInDB

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: EventCreate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Create a new event
    """
    event_service = EventService(db)
    event_data = event_in.dict()
    event_data["created_by"] = current_user.id
    return event_service.create(event_data)

@router.get("", response_model=List[Event])
def read_events(
    skip: int = 0,
    limit: int = 100,
    filter: Optional[EventFilter] = None,
    current_user: UserInDB = Depends(get_current_active_user),
    db: Database = Depends(get_db)
) -> Any:
    """
    Retrieve events with optional filtering
    """
    event_service = EventService(db)
    
    # Convert filter to dict and remove None values
    filter_dict = filter.dict(exclude_unset=True) if filter else {}
    
    # Regular users can only see their own events unless they have permission
    if not current_user.is_superuser:
        filter_dict["created_by"] = current_user.id
    
    return event_service.get_multi(
        skip=skip, 
        limit=limit,
        filters=filter_dict
    )

@router.get("/{event_id}", response_model=Event)
async def read_event(
    event_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get a specific event by id
    """
    event_service = EventService(db)
    event = await event_service.get(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only allow event creator or admin to view
    if event.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return event

@router.put("/{event_id}", response_model=Event)
async def update_event(
    event_id: int,
    event_in: EventUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update an event
    """
    event_service = EventService(db)
    event = await event_service.get(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only allow event creator or admin to update
    if event.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await event_service.update(
        event_id=event_id,
        event_update=event_in
    )

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an event
    """
    event_service = EventService(db)
    event = await event_service.get(event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only allow event creator or admin to delete
    if event.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    await event_service.delete(event_id=event_id)
    return None

@router.post("/{event_id}/end", response_model=Event)
async def end_event(
    event_id: int,
    event_end: EventEnd,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    End an event
    """
    event_service = EventService(db)
    
    try:
        # Try to end the event
        db_event = await event_service.end_event(event_id, event_end.end_time)
        return db_event
    except ValueError as e:
        if str(e) == "Event not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        elif str(e) == "Event is already ended":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is already ended"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

@router.get("/{event_id}/attendees", response_model=List[Any])
async def get_event_attendees(
    event_id: int,
    current_user: UserInDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get list of attendees for a specific event
    """
    event_service = EventService(db)
    
    # Check if event exists and user has permission
    event = await event_service.get(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if not current_user.is_superuser and event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await event_service.get_attendees(event_id=event_id)
