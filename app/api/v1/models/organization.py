from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from app.models.pyobjectid import PyObjectId

class OrganizationInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # owner_id: Optional[PyObjectId] = None # To be linked to a user later if needed

    class Config:
        json_encoders = {
            PyObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
        allow_population_by_field_name = True
        arbitrary_types_allowed = True # For PyObjectId
