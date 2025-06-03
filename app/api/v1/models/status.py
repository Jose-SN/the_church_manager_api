from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel

class StatusType(str):
    COURSE = 'Course'
    CHAPTER = 'Chapter'
    FILE = 'File'


class Status(BaseModel):
    id: Optional[ObjectId] = None
    parent_id: str
    parent_type: str
    percentage: str
    comment: Optional[str] = None
    rating: Optional[str] = None
    reward: Optional[str] = None
    created_by_id: str
    created_at: datetime = datetime.utcnow()
    modification_date: Optional[datetime] = None

    
    def to_dict(self):
        return {
            '_id': str(self._id) if self._id else None,
            'parent_id': self.parent_id,
            'parent_type': self.parent_type,
            'percentage': self.percentage,
            'comment': self.comment,
            'rating': self.rating,
            'reward': self.reward,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at,
            'modification_date': self.modification_date
        }
    
    def __repr__(self):
        return f"<Status(parent_id={self.parent_id}, parent_type={self.parent_type}, created_by={self.created_by_id})>"
