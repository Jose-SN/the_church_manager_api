from typing import List, Optional, Dict, Any
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime

from app.models.status import Status, StatusType # TODO: Update this import path
from app.schemas.status import StatusCreate, StatusUpdate, StatusOverview # TODO: Update this import path if necessary
from app.core.logging import logger

class StatusService:
    """Service for handling status-related operations."""
    
    def __init__(self, db: Database):
        self.db = db
        self.collection = self.db['status']

    def get_status_by_id(self, status_id: str) -> Optional[Status]:
        """
        Get a status record by ID.
        
        Args:
            status_id: ID of the status record to retrieve
            
        Returns:
            Status record if found, None otherwise
        """
        doc = self.collection.find_one({'_id': ObjectId(status_id)})
        if doc:
            return Status(**doc)
        return None

    def list_statuses(
        self,
        skip: int = 0,
        limit: int = 100,
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        created_by: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> List[Status]:
        """
        List status records with optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            parent_id: Filter by parent ID
            parent_type: Filter by parent type
            created_by: Filter by creator
            sort_by: Field to sort by
            sort_dir: Sort direction (asc/desc)
            
        Returns:
            List of Status records
        """
        query = {}
        
        if parent_id:
            query['parent_id'] = parent_id
        if parent_type:
            query['parent_type'] = parent_type
        if created_by:
            query['created_by'] = created_by
            
        sort_order = 1 if sort_dir == "asc" else -1
        cursor = self.collection.find(query).sort(sort_by, sort_order).skip(skip).limit(limit)
        return [Status(**doc) for doc in cursor]

    def create_status(self, status_data: StatusCreate) -> Status:
        """
        Create a new status record.
        
        Args:
            status_data: Status data to create
            
        Returns:
            Created Status record
        """
        status_dict = status_data.dict()
        status_dict['created_at'] = datetime.utcnow()
        result = self.collection.insert_one(status_dict)
        status = Status(**status_dict)
        status._id = result.inserted_id # type: ignore
        return status

    def update_status(self, status_id: str, status_data: StatusUpdate) -> Optional[Status]:
        """
        Update an existing status record.
        
        Args:
            status_id: ID of the status to update
            status_data: Status data to update
            
        Returns:
            Updated Status record if found, None otherwise
        """
        status_dict = status_data.dict(exclude_unset=True)
        result = self.collection.update_one(
            {'_id': ObjectId(status_id)},
            {'$set': status_dict}
        )
        if result.modified_count > 0:
            doc = self.collection.find_one({'_id': ObjectId(status_id)})
            if doc:
                return Status(**doc)
        return None

    def delete_status(self, status_id: str) -> bool:
        """
        Delete a status record.
        
        Args:
            status_id: ID of the status to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        result = self.collection.delete_one({'_id': ObjectId(status_id)})
        return result.deleted_count > 0

    def get_status_overview(self) -> StatusOverview:
        """
        Get overview statistics for statuses.
        
        Returns:
            Status overview statistics
        """
        # Pipeline for total counts and status distribution by parent_type
        main_pipeline = [
            {
                "$group": {
                    "_id": "$parent_type",
                    "total_for_type": { "$sum": 1 },
                    # Assuming 'status' is a field in your documents representing categorical status
                    "statuses_push": { 
                        "$push": "$status" # Push actual status values
                    }
                }
            },
            {
                "$unwind": {
                    "path": "$statuses_push",
                    "preserveNullAndEmptyArrays": True # Keep parent_types even if they have no statuses
                }
            },
            {
                "$group": {
                    "_id": {"parent_type": "$_id", "status_value": "$statuses_push"},
                    "count_for_status_value": {"$sum": 1},
                    "total_for_type": {"$first": "$total_for_type"} # Carry over total for parent_type
                }
            },
            {
                "$group": {
                    "_id": "$_id.parent_type",
                    "total": {"$first": "$total_for_type"},
                    "by_status_array": {
                        "$push": {
                            "k": "$_id.status_value",
                            "v": "$count_for_status_value"
                        }
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "parent_type": "$_id",
                    "total": 1,
                    "by_status": { "$arrayToObject": "$by_status_array" }
                }
            }
        ]
        main_result = list(self.collection.aggregate(main_pipeline))

        # Pipeline for average ratings by parent_type
        avg_ratings_pipeline = [
            {
                "$match": {
                    "rating": {"$ne": None, "$type": "number"} # Consider only documents with numeric ratings
                }
            },
            {
                "$group": {
                    "_id": "$parent_type",
                    "average_rating_for_type": {"$avg": "$rating"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "parent_type": "$_id",
                    "average_rating": "$average_rating_for_type"
                }
            }
        ]
        avg_ratings_result = list(self.collection.aggregate(avg_ratings_pipeline))
        avg_ratings_dict = {item['parent_type']: item['average_rating'] for item in avg_ratings_result}

        # Construct the StatusOverview object
        # Note: The schema StatusOverview has 'total_count', 'by_type', 'by_date', 'recent_updates', 'average_ratings'
        # Mapping 'total_statuses' to 'total_count' and 'by_parent_type' to 'by_type'
        
        total_overall_statuses = sum([r.get('total', 0) for r in main_result])
        
        by_type_dict = {
            r.get('parent_type'): {
                'total': r.get('total', 0),
                'by_status': r.get('by_status', {})
            }
            for r in main_result if r.get('parent_type') # Ensure parent_type is not None
        }

        return StatusOverview(
            total_count=total_overall_statuses,
            by_type=by_type_dict,
            average_ratings=avg_ratings_dict,
            by_date={},  # Initialize as per schema, calculation not implemented here
            recent_updates=[]  # Initialize as per schema, calculation not implemented here
        )
