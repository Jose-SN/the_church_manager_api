from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic_settings import BaseSettings

class FileBase(BaseModel):
    filename: str = Field(..., min_length=1)
    contentType: str
    size: int
    uploadDate: datetime
    metadata: Optional[Dict[str, Any]] = None
    userId: str
    organizationId: Optional[str] = None
    tags: List[str] = []
    status: str = "active"
    url: Optional[str] = None

class FileCreate(FileBase):
    pass

class FileUpdate(BaseModel):
    filename: Optional[str] = None
    contentType: Optional[str] = None
    size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None
    organizationId: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    url: Optional[str] = None

class FileInDB(FileBase):
    id: str
    created_at: datetime
    updated_at: datetime

class FileSearch(BaseModel):
    query: str
    tags: Optional[List[str]] = None
    organizationId: Optional[str] = None
    userId: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    skip: int = 0
