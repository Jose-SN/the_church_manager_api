from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_active_user, get_current_active_admin
from app.schemas.mail_template import MailTemplateCreate, MailTemplateInDB, MailTemplateUpdate
from app.api.v1.services.mail_template_service import MailTemplateService

router = APIRouter()

@router.post("/", response_model=MailTemplateInDB, status_code=status.HTTP_201_CREATED)
async def create_mail_template(
    template_in: MailTemplateCreate,
    current_user: UserInDB = Depends(get_current_active_admin)
) -> Any:
    """
    Create a new mail template (admin only)
    """
    template_service = MailTemplateService()
    return await template_service.create_template(
        template_in=template_in,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )

@router.get("/{template_id}", response_model=MailTemplateInDB)
async def get_mail_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get a mail template by ID
    """
    template_service = MailTemplateService()
    template = await template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check organization access
    if str(template.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this template"
        )
    
    return template

@router.get("/", response_model=List[MailTemplateInDB])
async def list_mail_templates(
    skip: int = 0,
    limit: int = 100,
    template_type: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    List all mail templates in the organization with optional filtering
    """
    template_service = MailTemplateService()
    return await template_service.list_templates(
        organization_id=current_user.organization_id,
        template_type=template_type,
        skip=skip,
        limit=limit
    )

@router.put("/{template_id}", response_model=MailTemplateInDB)
async def update_mail_template(
    template_id: str,
    template_in: MailTemplateUpdate,
    current_user: UserInDB = Depends(get_current_active_admin)
) -> Any:
    """
    Update a mail template (admin only)
    """
    template_service = MailTemplateService()
    template = await template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check organization access
    if str(template.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this template"
        )
    
    return await template_service.update_template(template_id, template_in)

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mail_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_admin)
) -> None:
    """
    Delete a mail template (admin only)
    """
    template_service = MailTemplateService()
    template = await template_service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Only organization admins or superusers can delete templates
    is_org_admin = any(role.name == "admin" for role in current_user.roles)
    
    if str(template.organization_id) != str(current_user.organization_id) or \
       (not is_org_admin and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this template"
        )
    
    await template_service.delete_template(template_id)
