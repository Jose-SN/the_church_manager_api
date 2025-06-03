from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event as EventModel
from app.schemas.event import EventCreate, EventUpdate, EventFilter

class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event_in: Dict[str, Any]) -> EventModel:
        db_event = EventModel(**event_in)
        self.db.add(db_event)
        await self.db.commit()
        await self.db.refresh(db_event)
        return db_event

    async def get(self, event_id: int) -> Optional[EventModel]:
        result = await self.db.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        return result.scalars().first()

    async def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[EventModel]:
        query = select(EventModel).offset(skip).limit(limit)
        
        if filters:
            conditions = []
            if "title" in filters and filters["title"]:
                conditions.append(EventModel.title.ilike(f"%{filters['title']}%"))
            if "location" in filters and filters["location"]:
                conditions.append(EventModel.location.ilike(f"%{filters['location']}%"))
            if "is_active" in filters and filters["is_active"] is not None:
                conditions.append(EventModel.is_active == filters["is_active"])
            if "ended" in filters and filters["ended"] is not None:
                conditions.append(EventModel.ended == filters["ended"])
            if "start_time_after" in filters and filters["start_time_after"]:
                conditions.append(EventModel.start_time >= filters["start_time_after"])
            if "start_time_before" in filters and filters["start_time_before"]:
                conditions.append(EventModel.start_time <= filters["start_time_before"])
            if "created_by" in filters and filters["created_by"]:
                conditions.append(EventModel.created_by == filters["created_by"])
                
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self, 
        db_event: EventModel, 
        event_in: Union[EventUpdate, Dict[str, Any]]
    ) -> EventModel:
        if isinstance(event_in, dict):
            update_data = event_in
        else:
            update_data = event_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_event, field, value)
            
        self.db.add(db_event)
        await self.db.commit()
        await self.db.refresh(db_event)
        return db_event

    async def delete(self, event_id: int) -> bool:
        result = await self.db.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        db_event = result.scalars().first()
        if db_event:
            await self.db.delete(db_event)
            await self.db.commit()
            return True
        return False

    async def end_event(self, event_id: int, end_time: Optional[datetime] = None) -> EventModel:
        """
        Mark an event as ended
        """
        # Get the event
        db_event = await self.get(event_id)
        if not db_event:
            raise ValueError("Event not found")
            
        # Check if already ended
        if db_event.ended:
            raise ValueError("Event is already ended")
            
        # Update the event
        update_data = {
            "ended": True,
            "end_time": end_time or datetime.utcnow(),
            "is_active": False
        }
        
        # Update checkouts for this event (if applicable)
        # This would be implemented based on your specific requirements
        # await self._update_checkouts_for_event(event_id)
        
        return await self.update(db_event, update_data)
    
    async def get_attendees(self, event_id: int) -> List[Any]:
        """
        Get list of attendees for a specific event
        """
        # This would be implemented based on your attendance model
        # For now, returning an empty list as a placeholder
        return []
