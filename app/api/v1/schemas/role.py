from typing import List, Optional
from pydantic import BaseModel

from app.schemas.permission import Permission as PermissionSchema

class RoleBase(BaseModel):
    """Base schema for role data"""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    pass

class RoleUpdate(BaseModel):
    """Schema for updating role data"""
    name: Optional[str] = None
    description: Optional[str] = None

class RoleInDBBase(RoleBase):
    """Base schema for role data in database"""
    id: int
    
    class Config:
        orm_mode = True

class Role(RoleInDBBase):
    """Schema for role data returned to clients"""
    permissions: List[PermissionSchema] = []

# Request/Response schemas
class RoleCreateRequest(RoleCreate):
    """Schema for role creation request"""
    permission_ids: List[int] = []

class RoleResponse(Role):
    """Schema for role response"""
    pass

class RoleUpdateRequest(RoleUpdate):
    """Schema for role update request"""
    permission_ids: Optional[List[int]] = None

class RoleListResponse(BaseModel):
    """Schema for listing roles"""
    items: List[Role]
    total: int
