from fastapi import APIRouter, Depends, HTTPException, status, Query
from pymongo.database import Database
from bson import ObjectId

from app.schemas.status import Status, StatusCreate, StatusUpdate, StatusOverview
from app.models.user import User
from app.services.status_service import StatusService
from app.api.deps import get_db, get_current_active_user
from app.core.logging import logger

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/get", response_model=List[Status])
def get_statuses(
    skip: int = 0,
    limit: int = 100,
    parent_id: Optional[str] = Query(None),
    parent_type: Optional[str] = Query(None),
    created_by: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Database = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of status records with optional filters.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        parent_id: Filter by parent ID
        parent_type: Filter by parent type
        created_by: Filter by creator
        sort_by: Field to sort by
        sort_dir: Sort direction (asc/desc)
    """
    service = StatusService(db)
    return service.list_statuses(
        skip=skip,
        limit=limit,
        parent_id=parent_id,
        parent_type=parent_type,
        created_by=created_by,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

@router.get("/get-overview", response_model=StatusOverview)
def get_status_overview(
    db: Database = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get an overview of status records."""
    service = StatusService(db)
    return service.get_status_overview()

@router.post("/save", response_model=Status, status_code=status.HTTP_201_CREATED)
def create_status(
    status_data: StatusCreate,
    db: Database = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new status record."""
    service = StatusService(db)
    return service.create_status(status_data)

@router.put("/update", response_model=Status)
def update_status(
    status_id: str,
    status_data: StatusUpdate,
    db: Database = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing status record."""
    service = StatusService(db)
    if not service.get_status_by_id(status_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status not found"
        )
    return service.update_status(status_id, status_data)

@router.delete("/delete/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_status(
    status_id: str,
    db: Database = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a status record."""
    service = StatusService(db)
    if not service.delete_status(status_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Status not found"
        )
