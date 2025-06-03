from typing import List
from pydantic import BaseModel

class PermissionBase(BaseModel):
    """Base schema for permission data"""
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    """Schema for creating a new permission"""
    pass

class PermissionUpdate(BaseModel):
    """Schema for updating permission data"""
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionInDBBase(PermissionBase):
    """Base schema for permission data in database"""
    id: int
    
    class Config:
        orm_mode = True

class Permission(PermissionInDBBase):
    """Schema for permission data returned to clients"""
    pass

# Request/Response schemas
class PermissionCreateRequest(PermissionCreate):
    """Schema for permission creation request"""
    pass

class PermissionResponse(Permission):
    """Schema for permission response"""
    pass

class PermissionListResponse(BaseModel):
    """Schema for listing permissions"""
    items: List[Permission]
    total: int
