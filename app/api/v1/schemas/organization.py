from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, EmailStr

class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the organization")
    description: Optional[str] = Field(None, max_length=500, description="Description of the organization")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email for the organization")
    website: Optional[HttpUrl] = Field(None, description="Website URL for the organization")

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None

class Organization(OrganizationBase):
    id: str = Field(..., description="Unique ID of the organization")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Pydantic V2, replaces orm_mode
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
