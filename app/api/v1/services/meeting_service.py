from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting as MeetingModel, MeetingAttendee
from app.models.user import User as UserModel
from app.schemas.meeting import MeetingCreate, MeetingInDB, MeetingUpdate, MeetingAttendeeStatus

class MeetingService:
    """Service for handling meeting and attendance operations"""
    
    async def create_meeting(
        self,
        meeting_in: MeetingCreate,
        created_by: str,
        organization_id: str,
        db: AsyncSession
    ) -> MeetingInDB:
        """
        Create a new meeting
        """
        # Check for overlapping meetings for the same room/location
        if meeting_in.room_id:
            overlapping = await self._check_meeting_overlap(
                room_id=meeting_in.room_id,
                start_time=meeting_in.start_time,
                end_time=meeting_in.end_time,
                db=db
            )
            
            if overlapping:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Room is already booked for this time slot"
                )
        
        # Create meeting
        meeting_data = meeting_in.dict()
        meeting_data['created_by'] = created_by
        meeting_data['organization_id'] = organization_id
        
        db_meeting = MeetingModel(**meeting_data)
        db.add(db_meeting)
        await db.commit()
        await db.refresh(db_meeting)
        
        # Add creator as attendee
        await self._add_attendee(
            meeting_id=db_meeting.id,
            user_id=created_by,
            status=MeetingAttendeeStatus.attending,
            db=db
        )
        
        return await self.get_meeting_with_attendees(str(db_meeting.id), db)
    
    async def get_meeting(
        self,
        meeting_id: str,
        db: AsyncSession
    ) -> Optional[MeetingInDB]:
        """
        Get a meeting by ID
        """
        result = await db.execute(
            select(MeetingModel).where(MeetingModel.id == meeting_id)
        )
        return result.scalars().first()
    
    async def get_meeting_with_attendees(
        self,
        meeting_id: str,
        db: AsyncSession
    ) -> Optional[Dict]:
        """
        Get a meeting with its attendees
        """
        # Get meeting
        meeting = await self.get_meeting(meeting_id, db)
        if not meeting:
            return None
        
        # Get attendees with user details
        result = await db.execute(
            select(
                UserModel.id,
                UserModel.first_name,
                UserModel.last_name,
                UserModel.email,
                MeetingAttendee.status
            )
            .join(MeetingAttendee, MeetingAttendee.user_id == UserModel.id)
            .where(MeetingAttendee.meeting_id == meeting_id)
        )
        
        attendees = []
        for row in result.all():
            attendees.append({
                'user_id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'status': row[4]
            })
        
        # Convert to dict and add attendees
        meeting_dict = {c.name: getattr(meeting, c.name) for c in meeting.__table__.columns}
        meeting_dict['attendees'] = attendees
        
        return meeting_dict
    
    async def list_meetings(
        self,
        organization_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = None
    ) -> List[Dict]:
        """
        List meetings with optional date filtering
        """
        query = select(MeetingModel).where(
            MeetingModel.organization_id == organization_id
        )
        
        # Apply date filters
        if start_date:
            query = query.where(MeetingModel.start_time >= start_date)
        if end_date:
            query = query.where(MeetingModel.end_time <= end_date)
        
        # Order by start time
        query = query.order_by(MeetingModel.start_time.desc())
        
        # Apply pagination
        result = await db.execute(query.offset(skip).limit(limit))
        meetings = result.scalars().all()
        
        # Get meeting details with attendee counts
        meetings_with_attendees = []
        for meeting in meetings:
            # Get attendee count
            attendee_count = await self._get_meeting_attendee_count(meeting.id, db)
            
            meeting_dict = {c.name: getattr(meeting, c.name) for c in meeting.__table__.columns}
            meeting_dict['attendee_count'] = attendee_count
            meetings_with_attendees.append(meeting_dict)
        
        return meetings_with_attendees
    
    async def update_meeting(
        self,
        meeting_id: str,
        meeting_in: MeetingUpdate,
        db: AsyncSession
    ) -> MeetingInDB:
        """
        Update a meeting
        """
        meeting = await self.get_meeting(meeting_id, db)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check for room availability if room or time is being updated
        if meeting_in.room_id or meeting_in.start_time or meeting_in.end_time:
            room_id = meeting_in.room_id or meeting.room_id
            start_time = meeting_in.start_time or meeting.start_time
            end_time = meeting_in.end_time or meeting.end_time
            
            if room_id:
                overlapping = await self._check_meeting_overlap(
                    room_id=room_id,
                    start_time=start_time,
                    end_time=end_time,
                    exclude_meeting_id=meeting_id,
                    db=db
                )
                
                if overlapping:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Room is already booked for this time slot"
                    )
        
        # Update fields
        update_data = meeting_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(meeting, field, value)
        
        meeting.updated_at = datetime.utcnow()
        
        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)
        
        return await self.get_meeting_with_attendees(meeting_id, db)
    
    async def delete_meeting(
        self,
        meeting_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete a meeting and its attendees
        """
        meeting = await self.get_meeting(meeting_id, db)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Delete attendees
        await db.execute(
            MeetingAttendee.__table__.delete()
            .where(MeetingAttendee.meeting_id == meeting_id)
        )
        
        # Delete meeting
        await db.delete(meeting)
        await db.commit()
        
        return True
    
    async def update_attendance(
        self,
        meeting_id: str,
        user_id: str,
        status: MeetingAttendeeStatus,
        db: AsyncSession
    ) -> Dict[str, str]:
        """
        Update attendance status for a meeting attendee
        """
        # Check if meeting exists
        meeting = await self.get_meeting(meeting_id, db)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found"
            )
        
        # Check if user exists
        result = await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if attendance record exists
        result = await db.execute(
            select(MeetingAttendee)
            .where(
                and_(
                    MeetingAttendee.meeting_id == meeting_id,
                    MeetingAttendee.user_id == user_id
                )
            )
        )
        attendee = result.scalars().first()
        
        if attendee:
            # Update existing attendance
            attendee.status = status
            attendee.updated_at = datetime.utcnow()
        else:
            # Create new attendance record
            attendee = MeetingAttendee(
                meeting_id=meeting_id,
                user_id=user_id,
                status=status
            )
        
        db.add(attendee)
        await db.commit()
        await db.refresh(attendee)
        
        return {"status": "success", "message": f"Attendance updated to {status.value}"}
    
    async def _add_attendee(
        self,
        meeting_id: str,
        user_id: str,
        status: MeetingAttendeeStatus,
        db: AsyncSession
    ) -> None:
        """
        Add an attendee to a meeting
        """
        attendee = MeetingAttendee(
            meeting_id=meeting_id,
            user_id=user_id,
            status=status
        )
        db.add(attendee)
        await db.commit()
    
    async def _get_meeting_attendee_count(
        self,
        meeting_id: str,
        db: AsyncSession
    ) -> int:
        """
        Get the number of attendees for a meeting
        """
        result = await db.execute(
            select(func.count(MeetingAttendee.id))
            .where(MeetingAttendee.meeting_id == meeting_id)
        )
        return result.scalar() or 0
    
    async def _check_meeting_overlap(
        self,
        room_id: str,
        start_time: datetime,
        end_time: datetime,
        db: AsyncSession,
        exclude_meeting_id: Optional[str] = None
    ) -> bool:
        """
        Check if there's an overlapping meeting in the same room
        """
        query = select(MeetingModel).where(
            and_(
                MeetingModel.room_id == room_id,
                or_(
                    # New meeting starts during existing meeting
                    and_(
                        MeetingModel.start_time <= start_time,
                        MeetingModel.end_time > start_time
                    ),
                    # New meeting ends during existing meeting
                    and_(
                        MeetingModel.start_time < end_time,
                        MeetingModel.end_time >= end_time
                    ),
                    # Existing meeting is within new meeting
                    and_(
                        MeetingModel.start_time >= start_time,
                        MeetingModel.end_time <= end_time
                    )
                )
            )
        )
        
        if exclude_meeting_id:
            query = query.where(MeetingModel.id != exclude_meeting_id)
        
        result = await db.execute(query)
        return result.scalars().first() is not None

# Singleton instance
meeting_service = MeetingService()

def get_meeting_service() -> MeetingService:
    return meeting_service
