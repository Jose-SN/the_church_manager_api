from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId

from app.core.security import get_password_hash, verify_password
from app.database.connection import get_database
from app.models.attendance import (
    AttendanceCreate, 
    AttendanceUpdate, 
    AttendanceInDB,
    AttendanceStats,
    AttendanceSummary
)
from app.models.user import UserInDB

class AttendanceService:
    """Service class for attendance operations."""
    
    def __init__(self):
        self.db = get_database()
        self.attendance_collection = self.db.attendance
        self.users_collection = self.db.users

    async def create_attendance(self, attendance_create: AttendanceCreate) -> AttendanceInDB:
        """
        Create a new attendance record.
        """
        # Validate user exists
        user = await self.users_collection.find_one({"_id": ObjectId(attendance_create.userId)})
        if not user:
            raise ValueError("User not found")
            
        # Validate event or meeting exists
        if attendance_create.eventId:
            event = await self.db.events.find_one({"_id": ObjectId(attendance_create.eventId)})
            if not event:
                raise ValueError("Event not found")
        elif attendance_create.meetingId:
            meeting = await self.db.meetings.find_one({"_id": ObjectId(attendance_create.meetingId)})
            if not meeting:
                raise ValueError("Meeting not found")
        
        # Create attendance document
        attendance_dict = attendance_create.model_dump()
        attendance_dict["created_at"] = datetime.utcnow()
        attendance_dict["updated_at"] = datetime.utcnow()
        
        # Insert attendance
        result = await self.attendance_collection.insert_one(attendance_dict)
        attendance = await self.attendance_collection.find_one({"_id": result.inserted_id})
        return AttendanceInDB(**attendance)

    async def get_attendance_by_id(self, attendance_id: str) -> Optional[AttendanceInDB]:
        """
        Get attendance record by ID.
        """
        attendance = await self.attendance_collection.find_one({"_id": ObjectId(attendance_id)})
        return AttendanceInDB(**attendance) if attendance else None

    async def get_attendance(
        self,
        user_id: Optional[str] = None,
        event_id: Optional[str] = None,
        meeting_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AttendanceInDB]:
        """
        Get list of attendance records.
        """
        query = {}
        if user_id:
            query["userId"] = user_id
        if event_id:
            query["eventId"] = event_id
        if meeting_id:
            query["meetingId"] = meeting_id
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            query["date"] = query.get("date", {})
            query["date"]["$lte"] = end_date
        
        attendances = await self.attendance_collection.find(query).skip(skip).limit(limit).to_list(100)
        return [AttendanceInDB(**attendance) for attendance in attendances]

    async def update_attendance(
        self, 
        attendance_id: str, 
        attendance_update: AttendanceUpdate
    ) -> AttendanceInDB:
        """
        Update attendance record.
        """
        # Check if attendance exists
        attendance = await self.get_attendance_by_id(attendance_id)
        if not attendance:
            raise ValueError("Attendance record not found")
            
        # Update attendance
        update_data = attendance_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        await self.attendance_collection.update_one(
            {"_id": ObjectId(attendance_id)},
            {"$set": update_data}
        )
        
        # Get updated attendance
        updated_attendance = await self.get_attendance_by_id(attendance_id)
        if not updated_attendance:
            raise ValueError("Attendance record not found after update")
        return updated_attendance

    async def delete_attendance(self, attendance_id: str) -> None:
        """
        Delete attendance record.
        """
        await self.attendance_collection.delete_one({"_id": ObjectId(attendance_id)})

    async def get_attendance_stats(
        self,
        event_id: Optional[str] = None,
        meeting_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AttendanceStats:
        """
        Get attendance statistics.
        """
        query = {}
        if event_id:
            query["eventId"] = event_id
        if meeting_id:
            query["meetingId"] = meeting_id
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            query["date"] = query.get("date", {})
            query["date"]["$lte"] = end_date
        
        # Get total count
        total = await self.attendance_collection.count_documents(query)
        
        # Get status counts
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        result = await self.attendance_collection.aggregate(pipeline).to_list(100)
        status_counts = {item["_id"]: item["count"] for item in result}
        
        # Calculate percentages
        percentage = (status_counts.get("present", 0) / total * 100) if total > 0 else 0
        
        return AttendanceStats(
            total=total,
            present=status_counts.get("present", 0),
            absent=status_counts.get("absent", 0),
            late=status_counts.get("late", 0),
            percentage=percentage
        )

    async def get_attendance_summary(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "daily"  # daily, weekly, monthly
    ) -> List[AttendanceSummary]:
        """
        Get attendance summary by period.
        """
        query = {"organizationId": organization_id}
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            query["date"] = query.get("date", {})
            query["date"]["$lte"] = end_date
        
        # Determine date grouping
        date_group = {
            "daily": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "weekly": {"$dateToString": {"format": "%Y-%U", "date": "$date"}},
            "monthly": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}
        }[period]
        
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": date_group,
                "total": {"$sum": 1},
                "present": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "present"]}, 1, 0]
                    }
                },
                "absent": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "absent"]}, 1, 0]
                    }
                },
                "late": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", "late"]}, 1, 0]
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.attendance_collection.aggregate(pipeline).to_list(100)
        
        summaries = []
        for item in results:
            date = datetime.strptime(item["_id"], 
                "%Y-%m-%d" if period == "daily" else 
                "%Y-%U" if period == "weekly" else 
                "%Y-%m")
            
            percentage = (item["present"] / item["total"] * 100) if item["total"] > 0 else 0
            
            summaries.append(AttendanceSummary(
                date=date,
                total=item["total"],
                present=item["present"],
                absent=item["absent"],
                late=item["late"],
                percentage=percentage
            ))
            
        return summaries

    async def get_not_attended_users(
        self,
        event_id: Optional[str] = None,
        meeting_id: Optional[str] = None,
        organization_id: str = None
    ) -> List[UserInDB]:
        """
        Get users who did not attend a specific event or meeting.
        """
        # Get users who attended
        attended_users = await self.attendance_collection.find({
            "$or": [
                {"eventId": event_id} if event_id else {},
                {"meetingId": meeting_id} if meeting_id else {}
            ]
        }).distinct("userId")
        
        # Get all users from organization who are not in the attended list
        users = await self.users_collection.find({
            "_id": {"$nin": attended_users},
            "organizationId": organization_id
        }).to_list(100)
        
        return [UserInDB(**user) for user in users]
