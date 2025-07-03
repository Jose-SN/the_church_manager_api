from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class MeetingDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    date: str
    speechBy: Optional[str] = None
    location: str
    language: Optional[str] = None
    videoURL: str
    submittedBy: Optional[PyObjectId] = None
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    modification_date: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Sunday Service",
                "date": "2023-06-11T10:00:00",
                "speechBy": "Pastor John",
                "location": "Main Hall",
                "language": "English",
                "videoURL": "https://example.com/video123",
                "submittedBy": "507f1f77bcf86cd799439011"
            }
        }