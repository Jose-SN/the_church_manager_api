from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.security import get_current_active_user
from app.schemas.file import FileInDB
from app.api.v1.services.file_service import FileService

router = APIRouter()

@router.post("/upload", response_model=FileInDB)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Upload a file
    """
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_service = FileService()
    try:
        return await file_service.upload_file(
            file=file,
            uploaded_by=current_user.id,
            organization_id=current_user.organization_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{file_id}", response_class=FileResponse)
async def download_file(
    file_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Download a file by ID
    """
    file_service = FileService()
    file_info = await file_service.get_file_info(file_id)
    
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check permissions
    if str(file_info.organization_id) != str(current_user.organization_id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this file"
        )
    
    return await file_service.download_file(file_id)

@router.get("/list/all", response_model=List[FileInDB])
async def list_files(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    List all files in the organization
    """
    file_service = FileService()
    return await file_service.list_files(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit
    )

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> None:
    """
    Delete a file by ID
    """
    file_service = FileService()
    file_info = await file_service.get_file_info(file_id)
    
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Only allow deletion by organization admins or file owner
    is_org_admin = any(role.name == "admin" for role in current_user.roles)
    is_file_owner = str(file_info.uploaded_by) == str(current_user.id)
    
    if not (is_org_admin or is_file_owner or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this file"
        )
    
    await file_service.delete_file(file_id)
