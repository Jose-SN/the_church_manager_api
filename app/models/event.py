from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    ended = Column(Boolean, default=False)
    
    # Relationships
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="events_created")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    attendees = relationship("Attendance", back_populates="event")
