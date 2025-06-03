from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_active_user, get_current_active_admin
from app.schemas.guest import GuestCreate, GuestInDB, GuestUpdate
from app.api.v1.services.guest_service import GuestService

router = APIRouter()

@router.post("/", response_model=GuestInDB, status_code=status.HTTP_201_CREATED)
async def create_guest(
    guest_in: GuestCreate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Create a new guest
    """
    guest_service = GuestService()
    return await guest_service.create_guest(
        guest_in=guest_in,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/{guest_id}", response_model=GuestInDB)
async def get_guest(
    guest_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get a guest by ID
    """
    guest_service = GuestService()
    guest = await guest_service.get_guest(guest_id)
    
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Check organization access
    if str(guest.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this guest"
        )
    
    return guest

@router.get("/", response_model=List[GuestInDB])
async def list_guests(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    List all guests in the organization with optional search
    """
    guest_service = GuestService()
    return await guest_service.list_guests(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit,
        search=search
    )

@router.put("/{guest_id}", response_model=GuestInDB)
async def update_guest(
    guest_id: str,
    guest_in: GuestUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Update a guest
    """
    guest_service = GuestService()
    guest = await guest_service.get_guest(guest_id)
    
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Check organization access
    if str(guest.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this guest"
        )
    
    return await guest_service.update_guest(guest_id, guest_in)

@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guest(
    guest_id: str,
    current_user: UserInDB = Depends(get_current_active_admin)
) -> None:
    """
    Delete a guest (admin only)
    """
    guest_service = GuestService()
    guest = await guest_service.get_guest(guest_id)
    
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest not found"
        )
    
    # Only organization admins or superusers can delete guests
    is_org_admin = any(role.name == "admin" for role in current_user.roles)
    
    if str(guest.organization_id) != str(current_user.organization_id) or \
       (not is_org_admin and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this guest"
        )
    
    await guest_service.delete_guest(guest_id)
