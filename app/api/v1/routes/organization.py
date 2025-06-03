from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Any
from pymongo.database import Database

from app.core.security import get_current_active_user
from app.models.user import UserInDB # Assuming UserInDB is the correct model for current_user
from app.schemas.organization import Organization, OrganizationCreate, OrganizationUpdate
from app.services.organization_service import OrganizationService
from app.db.mongodb import get_db

router = APIRouter()

@router.post("/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED, tags=["organizations"])
def create_organization(
    org_create: OrganizationCreate,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # For future permission checks
) -> Any:
    """
    Create new organization.
    """
    service = OrganizationService(db)
    organization = service.create_organization(org_create=org_create)
    return organization

@router.get("/organizations", response_model=List[Organization], tags=["organizations"])
def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # For future permission checks
) -> Any:
    """
    Get list of organizations with pagination.
    """
    service = OrganizationService(db)
    organizations = service.list_organizations(skip=skip, limit=limit)
    return organizations

@router.get("/organizations/{organization_id}", response_model=Organization, tags=["organizations"])
def get_organization(
    organization_id: str,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # For future permission checks
) -> Any:
    """
    Get specific organization by ID.
    """
    service = OrganizationService(db)
    organization = service.get_organization_by_id(org_id=organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return organization

@router.put("/organizations/{organization_id}", response_model=Organization, tags=["organizations"])
def update_organization(
    organization_id: str,
    org_update: OrganizationUpdate,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # For future permission checks
) -> Any:
    """
    Update existing organization.
    """
    service = OrganizationService(db)
    updated_organization = service.update_organization(org_id=organization_id, org_update=org_update)
    if not updated_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or no changes made",
        )
    return updated_organization

@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["organizations"])
def delete_organization(
    organization_id: str,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user) # For future permission checks
) -> None:
    """
    Delete organization.
    """
    service = OrganizationService(db)
    deleted = service.delete_organization(org_id=organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return None
