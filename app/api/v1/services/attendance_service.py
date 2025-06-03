from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo.database import Database
from pymongo.collection import Collection
from bson import ObjectId

from app.api.v1.models.attendance import (
    AttendanceInDB,
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceStatus, 
    AttendanceStats,
    AttendanceSummaryItem
)
from app.api.v1.models.user import UserInDB 
from app.core.logging import logger

class AttendanceService:
    """Service for handling attendance-related operations."""
    
    def __init__(self, db: Database):
        self.db = db
        self.collection: Collection = self.db['attendance']
        self.users_collection: Collection = self.db['users']
        self.events_collection: Collection = self.db['events']
        self.meetings_collection: Collection = self.db['meetings']

    def create_attendance(self, attendance_create: AttendanceCreate) -> AttendanceInDB:
        """Create a new attendance record."""
        try:
            user_obj_id = ObjectId(attendance_create.user_id)
            parent_obj_id = ObjectId(attendance_create.parent_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId provided for user_id or parent_id: {e}")
            raise ValueError("Invalid user_id or parent_id format")

        user = self.users_collection.find_one({"_id": user_obj_id})
        if not user:
            raise ValueError(f"User not found with ID: {attendance_create.user_id}")

        if attendance_create.parent_type == "event":
            parent_doc = self.events_collection.find_one({"_id": parent_obj_id})
            if not parent_doc:
                raise ValueError(f"Event not found with ID: {attendance_create.parent_id}")
        elif attendance_create.parent_type == "meeting":
            parent_doc = self.meetings_collection.find_one({"_id": parent_obj_id})
            if not parent_doc:
                raise ValueError(f"Meeting not found with ID: {attendance_create.parent_id}")
        else:
            raise ValueError(f"Invalid parent_type: {attendance_create.parent_type}")

        now = datetime.utcnow()
        attendance_doc = attendance_create.model_dump(exclude_unset=True)
        attendance_doc['user_id'] = user_obj_id
        attendance_doc['parent_id'] = parent_obj_id
        attendance_doc['created_at'] = now
        attendance_doc['updated_at'] = now
        
        if isinstance(attendance_doc.get('status'), AttendanceStatus):
            attendance_doc['status'] = attendance_doc['status'].value
        elif 'status' not in attendance_doc: # Default status if not provided
             attendance_doc['status'] = AttendanceStatus.PRESENT.value

        result = self.collection.insert_one(attendance_doc)
        created_doc_from_db = self.collection.find_one({'_id': result.inserted_id})
        if not created_doc_from_db:
            logger.error("Failed to retrieve attendance record after creation")
            raise Exception("Failed to retrieve attendance record after creation")
        return AttendanceInDB(**created_doc_from_db)

    def get_attendance_by_id(self, attendance_id: str) -> Optional[AttendanceInDB]:
        """Get an attendance record by ID."""
        try:
            obj_id = ObjectId(attendance_id)
        except Exception:
            logger.warning(f"Invalid ObjectId format for attendance_id: {attendance_id}")
            return None
        doc = self.collection.find_one({'_id': obj_id})
        return AttendanceInDB(**doc) if doc else None

    def get_attendance_by_user_and_parent(
        self, 
        user_id: str, 
        parent_id: str, 
        parent_type: str
    ) -> Optional[AttendanceInDB]:
        """Get attendance record by user and parent (event/meeting)."""
        try:
            user_obj_id = ObjectId(user_id)
            parent_obj_id = ObjectId(parent_id)
        except Exception:
            logger.warning("Invalid ObjectId format for user_id or parent_id in get_attendance_by_user_and_parent")
            return None

        doc = self.collection.find_one({
            'user_id': user_obj_id,
            'parent_id': parent_obj_id,
            'parent_type': parent_type
        })
        return AttendanceInDB(**doc) if doc else None

    def list_attendance(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        status: Optional[AttendanceStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AttendanceInDB]:
        """List attendance records with optional filtering."""
        query: Dict[str, Any] = {}
        try:
            if user_id is not None: query['user_id'] = ObjectId(user_id)
            if parent_id is not None: query['parent_id'] = ObjectId(parent_id)
        except Exception:
            logger.warning("Invalid ObjectId format in list_attendance filters.")
            return [] 
        if parent_type is not None: query['parent_type'] = parent_type
        if status is not None: query['status'] = status.value
        
        date_query: Dict[str, Any] = {}
        if start_date is not None: date_query['$gte'] = start_date
        if end_date is not None: date_query['$lte'] = end_date
        if date_query: query['created_at'] = date_query
        
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return [AttendanceInDB(**doc) for doc in cursor]

    def update_attendance(
        self,
        attendance_id: str,
        attendance_update: AttendanceUpdate
    ) -> Optional[AttendanceInDB]:
        """Update an attendance record."""
        try:
            obj_id = ObjectId(attendance_id)
        except Exception:
            logger.warning(f"Invalid ObjectId format for update: {attendance_id}")
            return None

        update_data = attendance_update.model_dump(exclude_unset=True)
        if not update_data:
            return self.get_attendance_by_id(attendance_id) 
            
        update_data['updated_at'] = datetime.utcnow()
        
        if 'status' in update_data and isinstance(update_data['status'], AttendanceStatus):
            update_data['status'] = update_data['status'].value

        for immutable_field in ['user_id', 'parent_id', 'parent_type', 'created_at']:
            if immutable_field in update_data: del update_data[immutable_field]
        
        result = self.collection.update_one({'_id': obj_id}, {'$set': update_data})
        
        if result.matched_count == 0:
            logger.warning(f"Attendance record not found for update: {attendance_id}")
            return None
        
        updated_doc = self.collection.find_one({'_id': obj_id})
        return AttendanceInDB(**updated_doc) if updated_doc else None

    def delete_attendance(self, attendance_id: str) -> bool:
        """Delete an attendance record."""
        try:
            obj_id = ObjectId(attendance_id)
        except Exception:
            logger.warning(f"Invalid ObjectId format for delete: {attendance_id}")
            return False
        result = self.collection.delete_one({'_id': obj_id})
        if result.deleted_count == 0:
            logger.warning(f"Attendance record not found for deletion: {attendance_id}")
            return False
        return True

    def bulk_create_attendance(
        self,
        attendance_creates: List[AttendanceCreate]
    ) -> List[AttendanceInDB]:
        """Create multiple attendance records in bulk."""
        if not attendance_creates: return []
        docs_to_insert = []
        now = datetime.utcnow()
        for i, data_create in enumerate(attendance_creates):
            try:
                user_obj_id = ObjectId(data_create.user_id)
                parent_obj_id = ObjectId(data_create.parent_id)
            except Exception:
                logger.warning(f"Skipping invalid ObjectId in bulk create for item {i}: user_id={data_create.user_id}, parent_id={data_create.parent_id}")
                continue
            doc = data_create.model_dump(exclude_unset=True)
            doc['user_id'] = user_obj_id
            doc['parent_id'] = parent_obj_id
            doc['created_at'] = now
            doc['updated_at'] = now
            if 'status' in doc and isinstance(doc['status'], AttendanceStatus):
                 doc['status'] = doc['status'].value
            elif 'status' not in doc:
                 doc['status'] = AttendanceStatus.PRESENT.value # Default status
            docs_to_insert.append(doc)

        if not docs_to_insert: return []
        try:
            result = self.collection.insert_many(docs_to_insert, ordered=False)
            created_docs_cursor = self.collection.find({'_id': {'$in': result.inserted_ids}})
            return [AttendanceInDB(**doc) for doc in created_docs_cursor]
        except Exception as e:
            logger.error(f"Error in bulk attendance creation: {str(e)}")
            if hasattr(e, 'details') and 'writeErrors' in e.details: # type: ignore
                 logger.error(f"Bulk write errors: {e.details['writeErrors']}") # type: ignore
            # Attempt to return any that were inserted if IDs are available from a partial write with ordered=False
            # This depends on the driver's behavior for BulkWriteError with ordered=False.
            # A common pattern is that `result` might not be available or fully populated if insert_many itself raises an error.
            # For simplicity, we'll return empty list on major error. A more complex recovery could be attempted.
            return []

    def get_attendance_stats(
        self,
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AttendanceStats:
        """Get attendance statistics."""
        query: Dict[str, Any] = {}
        if parent_id and parent_type:
            try: query["parent_id"] = ObjectId(parent_id)
            except Exception: 
                logger.warning(f"Invalid parent_id format in get_attendance_stats: {parent_id}")
                return AttendanceStats(total=0, present=0, absent=0, late=0, excused=0, percentage=0.0)
            query["parent_type"] = parent_type

        date_filter: Dict[str, Any] = {}
        if start_date: date_filter["$gte"] = start_date
        if end_date: date_filter["$lte"] = end_date
        if date_filter: query["created_at"] = date_filter
        
        total = self.collection.count_documents(query)
        pipeline = [
            {"$match": query},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        result_agg = list(self.collection.aggregate(pipeline))
        status_counts: Dict[str, int] = {item["_id"]: item["count"] for item in result_agg}
        
        present_count = status_counts.get(AttendanceStatus.PRESENT.value, 0)
        absent_count = status_counts.get(AttendanceStatus.ABSENT.value, 0)
        late_count = status_counts.get(AttendanceStatus.LATE.value, 0)
        excused_count = status_counts.get(AttendanceStatus.EXCUSED.value, 0)
        percentage = (present_count / total * 100) if total > 0 else 0.0
        
        return AttendanceStats(
            total=total, present=present_count, absent=absent_count,
            late=late_count, excused=excused_count, percentage=round(percentage, 2)
        )

    def get_attendance_summary(
        self,
        parent_type_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "daily"
    ) -> List[AttendanceSummaryItem]:
        """Get attendance summary by period."""
        query: Dict[str, Any] = {}
        if parent_type_filter: query["parent_type"] = parent_type_filter
        date_filter: Dict[str, Any] = {}
        if start_date: date_filter["$gte"] = start_date
        if end_date: date_filter["$lte"] = end_date
        if date_filter: query["created_at"] = date_filter

        if period not in ["daily", "weekly", "monthly"]:
            raise ValueError("Period must be 'daily', 'weekly', or 'monthly'")
        date_group_format = {"daily": "%Y-%m-%d", "weekly": "%Y-%U", "monthly": "%Y-%m"}[period]
        
        pipeline: List[Dict[str, Any]] = [
            {"$match": query},
            {"$group": {
                "_id": {"$dateToString": {"format": date_group_format, "date": "$created_at"}},
                "total": {"$sum": 1},
                "present": {"$sum": {"$cond": [{"$eq": ["$status", AttendanceStatus.PRESENT.value]}, 1, 0]}},
                "absent": {"$sum": {"$cond": [{"$eq": ["$status", AttendanceStatus.ABSENT.value]}, 1, 0]}},
                "late": {"$sum": {"$cond": [{"$eq": ["$status", AttendanceStatus.LATE.value]}, 1, 0]}},
                "excused": {"$sum": {"$cond": [{"$eq": ["$status", AttendanceStatus.EXCUSED.value]}, 1, 0]}}
            }},
            {"$sort": {"_id": 1}}
        ]
        results_agg = list(self.collection.aggregate(pipeline))
        summaries: List[AttendanceSummaryItem] = []
        for item in results_agg:
            period_date_str = item["_id"]
            total_count = item.get("total", 0)
            present_count = item.get("present", 0)
            percentage = (present_count / total_count * 100) if total_count > 0 else 0.0
            summaries.append(AttendanceSummaryItem(
                period=period_date_str, total=total_count, present=present_count,
                absent=item.get("absent",0), late=item.get("late",0),
                excused=item.get("excused",0), percentage=round(percentage, 2)
            ))
        return summaries

    def get_not_attended_users(
        self,
        parent_id: str,
        parent_type: str,
        expected_user_ids: List[str]
    ) -> List[str]:
        """Get user IDs who did not attend a specific event/meeting from a list of expected attendees."""
        if not expected_user_ids: return []
        try:
            parent_obj_id = ObjectId(parent_id)
            expected_obj_ids = [ObjectId(uid) for uid in expected_user_ids if ObjectId.is_valid(uid)]
            if len(expected_obj_ids) != len(expected_user_ids):
                logger.warning("Some user_ids were invalid in get_not_attended_users")
        except Exception as e:
            logger.error(f"Error with ObjectIds in get_not_attended_users: {e}")
            return expected_user_ids 

        attended_users_cursor = self.collection.find({
            "parent_id": parent_obj_id,
            "parent_type": parent_type,
            "user_id": {"$in": expected_obj_ids},
            "status": AttendanceStatus.PRESENT.value 
        }, {"user_id": 1})
        
        attended_user_ids_set = {str(doc['user_id']) for doc in attended_users_cursor}
        not_attended_user_ids = [uid_str for uid_str in expected_user_ids if uid_str not in attended_user_ids_set]
        return not_attended_user_ids
