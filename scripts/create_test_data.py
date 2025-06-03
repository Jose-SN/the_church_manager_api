import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.user import User, Role, Event, EventAttendance
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test users
TEST_USERS = [
    {
        "email": "pastor@example.com",
        "full_name": "John Pastor",
        "password": "pastor123",
        "is_active": True,
        "is_superuser": False,
        "roles": ["pastor"]
    },
    {
        "email": "member1@example.com",
        "full_name": "Jane Member",
        "password": "member123",
        "is_active": True,
        "is_superuser": False,
        "roles": ["member"]
    },
    {
        "email": "member2@example.com",
        "full_name": "Bob Member",
        "password": "member123",
        "is_active": True,
        "is_superuser": False,
        "roles": ["member"]
    },
]

# Test events
TEST_EVENTS = [
    {
        "title": "Sunday Service",
        "description": "Weekly Sunday worship service",
        "start_time": datetime.utcnow() + timedelta(days=2, hours=10),
        "end_time": datetime.utcnow() + timedelta(days=2, hours=12),
        "location": "Main Sanctuary",
        "is_active": True,
        "creator_email": "pastor@example.com"
    },
    {
        "title": "Bible Study",
        "description": "Mid-week Bible study group",
        "start_time": datetime.utcnow() + timedelta(days=4, hours=18),
        "end_time": datetime.utcnow() + timedelta(days=4, hours=20),
        "location": "Fellowship Hall",
        "is_active": True,
        "creator_email": "pastor@example.com"
    },
]

async def create_test_users(session: AsyncSession, roles: dict) -> dict:
    """Create test users"""
    logger.info("Creating test users...")
    users = {}
    
    for user_data in TEST_USERS:
        result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        user = result.scalars().first()
        
        if not user:
            user_roles = [roles[role_name] for role_name in user_data["roles"]]
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=get_password_hash(user_data["password"]),
                is_active=user_data["is_active"],
                is_superuser=user_data.get("is_superuser", False),
                roles=user_roles
            )
            session.add(user)
            logger.info(f"Created test user: {user_data['email']}")
        else:
            logger.info(f"Test user already exists: {user_data['email']}")
        
        users[user_data["email"]] = user
    
    await session.commit()
    return users

async def create_test_events(session: AsyncSession, users: dict) -> None:
    """Create test events"""
    logger.info("Creating test events...")
    
    for event_data in TEST_EVENTS:
        creator = users.get(event_data["creator_email"])
        if not creator:
            logger.warning(f"Creator not found for event: {event_data['title']}")
            continue
            
        result = await session.execute(
            select(Event).where(Event.title == event_data["title"])
        )
        event = result.scalars().first()
        
        if not event:
            event = Event(
                title=event_data["title"],
                description=event_data["description"],
                start_time=event_data["start_time"],
                end_time=event_data["end_time"],
                location=event_data["location"],
                is_active=event_data["is_active"],
                creator_id=creator.id
            )
            session.add(event)
            logger.info(f"Created test event: {event_data['title']}")
        else:
            logger.info(f"Test event already exists: {event_data['title']}")
    
    await session.commit()

async def create_test_attendance(session: AsyncSession, users: dict) -> None:
    """Create test attendance records"""
    logger.info("Creating test attendance records...")
    
    # Get all events
    result = await session.execute(select(Event))
    events = result.scalars().all()
    
    # For each event, create attendance records for some users
    for event in events:
        for email, user in users.items():
            if email == "admin@thechurchmanager.com":
                continue  # Skip admin user
                
            # Randomly decide if user attends this event (50% chance)
            import random
            if random.random() < 0.5:
                result = await session.execute(
                    select(EventAttendance)
                    .where(EventAttendance.event_id == event.id)
                    .where(EventAttendance.user_id == user.id)
                )
                attendance = result.scalars().first()
                
                if not attendance:
                    attendance = EventAttendance(
                        event_id=event.id,
                        user_id=user.id,
                        attended=random.random() > 0.2,  # 80% chance of attending
                        notes=f"Test attendance for {user.full_name}"
                    )
                    session.add(attendance)
                    logger.info(f"Created attendance record for {user.email} at {event.title}")
    
    await session.commit()

async def main() -> None:
    """Main function to create test data"""
    logger.info("Starting test data creation...")
    
    async with async_session_factory() as session:
        try:
            # Get roles
            result = await session.execute(select(Role))
            roles = {role.name: role for role in result.scalars().all()}
            
            # Create test users
            users = await create_test_users(session, roles)
            
            # Create test events
            await create_test_events(session, users)
            
            # Create test attendance records
            await create_test_attendance(session, users)
            
            logger.info("Test data creation completed successfully")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating test data: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
