from datetime import datetime
from typing import Any

from sqlalchemy.ext.declarative import as_declared_api, declared_attr
from sqlalchemy import Column, Integer, DateTime

class Base:
    """Base class for all database models"""
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # Common columns
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.id}>"
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
