from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pymongo.database import Database
from bson import ObjectId
from app.models.pyobjectid import PyObjectId # TODO: Update this import path

from app.schemas.event import Event, EventCreate, EventUpdate, EventFilter # TODO: Update this import path if necessary

class EventService:
    def __init__(self, db: Database):
        self.db = db
        self.collection = self.db['events']

    def create(self, event_in: Dict[str, Any], current_user_id: Optional[PyObjectId] = None) -> Event:
        # Ensure created_at is set
        event_data = event_in.copy()
        event_data['created_at'] = event_data.get('created_at', datetime.utcnow())
        
        # Set created_by if current_user_id is provided and not already in event_data
        if current_user_id and 'created_by' not in event_data:
            event_data['created_by'] = current_user_id
        elif 'created_by' in event_data and isinstance(event_data['created_by'], str):
            try:
                event_data['created_by'] = ObjectId(event_data['created_by'])
            except Exception:
                # Handle invalid ObjectId string for created_by if necessary, or let Pydantic validation catch it
                pass 

        # Remove 'id' or '_id' from input if present, as MongoDB will generate it
        event_data.pop('id', None)
        event_data.pop('_id', None)

        result = self.collection.insert_one(event_data)
        created_event_doc = self.collection.find_one({'_id': result.inserted_id})
        if created_event_doc:
            return Event(**created_event_doc)
        # This case should ideally not happen if insert_one was successful
        raise Exception("Failed to create or retrieve event after insertion")

    def get(self, event_id: str) -> Optional[Event]:
        doc = self.collection.find_one({'_id': ObjectId(event_id)})
        if doc:
            return Event(**doc)
        return None

    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Event]:
        query = {}
        
        if filters:
            if "title" in filters and filters["title"]:
                query["title"] = {"$regex": f"{filters['title']}", "$options": "i"}
            if "location" in filters and filters["location"]:
                query["location"] = {"$regex": f"{filters['location']}", "$options": "i"}
            if "is_active" in filters and filters["is_active"] is not None:
                query["is_active"] = filters["is_active"]
            if "ended" in filters and filters["ended"] is not None:
                query["ended"] = filters["ended"]
            if "start_time_after" in filters and filters["start_time_after"]:
                query["start_time"] = {"$gte": filters["start_time_after"]}
            if "start_time_before" in filters and filters["start_time_before"]:
                query["start_time"] = {"$lte": filters["start_time_before"]}
            if "created_by" in filters and filters["created_by"]:
                query["created_by"] = ObjectId(filters["created_by"])
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        return [Event(**doc) for doc in cursor]

    def update(
        self, 
        db_event: Event, 
        event_in: Union[EventUpdate, Dict[str, Any]]
    ) -> Event:
        """
        Update an event
        """
        if isinstance(event_in, dict):
            update_data = event_in
        else:
            update_data = event_in.dict(exclude_unset=True)
        
        if update_data:
            update_data['modification_date'] = datetime.utcnow()
            self.collection.update_one(
                {'_id': db_event._id},
                {'$set': update_data}
            )
            db_event = self.get(str(db_event._id))
        
        return db_event

    def remove(self, event_id: str) -> None:
        """
        Soft delete an event by setting is_active to False
        """
        self.collection.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': {'is_active': False}}
        )

    def end_event(self, event_id: str, end_time: datetime) -> None:
        """
        Mark an event as ended with the specified end time
        """
        self.collection.update_one(
            {'_id': ObjectId(event_id)},
            {'$set': {'ended': True, 'end_time': end_time}}
        )
    
    def get_attendees(self, event_id: str) -> List[Any]:
        """
        Get list of attendees for a specific event
        """
        # This would be implemented based on your attendance model and MongoDB queries
        # For now, returning an empty list as a placeholder.
        # Example placeholder for fetching attendees (assuming an 'attendance' collection):
        # attendees_cursor = self.db['attendance'].find({'event_id': ObjectId(event_id)})
        # return [attendee for attendee in attendees_cursor]
        return []
