import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.attendance_service import AttendanceService
from app.models.attendance import Attendance as AttendanceModel
from app.models.user import User
from app.models.event import Event
from app.schemas.attendance import (
    AttendanceCreate, 
    AttendanceUpdate, 
    AttendanceStatus,
    AttendanceStats,
    AttendanceSummary
)

# Test data
TEST_USER_ID = 1
TEST_EVENT_ID = 1
TEST_ATTENDANCE_ID = 1

def create_mock_attendance(**kwargs):
    """Helper to create a mock attendance object."""
    defaults = {
        'id': TEST_ATTENDANCE_ID,
        'user_id': TEST_USER_ID,
        'event_id': TEST_EVENT_ID,
        'status': AttendanceStatus.PRESENT,
        'recorded_by': 1,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    defaults.update(kwargs)
    return AttendanceModel(**defaults)

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock the query methods
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    return session

@pytest.mark.asyncio
async def test_create_attendance(mock_db_session):
    """Test creating a new attendance record."""
    # Setup
    service = AttendanceService(mock_db_session)
    attendance_data = {
        'user_id': TEST_USER_ID,
        'event_id': TEST_EVENT_ID,
        'status': 'present',
        'recorded_by': 1
    }
    
    # Mock the query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    # Mock the commit refresh
    created_attendance = create_mock_attendance(**attendance_data)
    mock_db_session.refresh.return_value = created_attendance
    
    # Test
    result = await service.create(attendance_data)
    
    # Assert
    assert result is not None
    assert result.user_id == TEST_USER_ID
    assert result.event_id == TEST_EVENT_ID
    assert result.status == 'present'
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    assert mock_db_session.refresh.called

@pytest.mark.asyncio
async def test_get_attendance_by_id(mock_db_session):
    """Test getting an attendance record by ID."""
    # Setup
    service = AttendanceService(mock_db_session)
    mock_attendance = create_mock_attendance()
    
    # Mock the query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_attendance
    mock_db_session.execute.return_value = mock_result
    
    # Test
    result = await service.get_attendance_by_id(TEST_ATTENDANCE_ID)
    
    # Assert
    assert result is not None
    assert result.id == TEST_ATTENDANCE_ID
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_update_attendance(mock_db_session):
    """Test updating an attendance record."""
    # Setup
    service = AttendanceService(mock_db_session)
    mock_attendance = create_mock_attendance()
    
    # Mock the get_attendance_by_id method
    service.get_attendance_by_id = AsyncMock(return_value=mock_attendance)
    
    # Test data
    update_data = {'status': 'absent'}
    
    # Test
    result = await service.update(TEST_ATTENDANCE_ID, update_data)
    
    # Assert
    assert result is not None
    assert result.status == 'absent'
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    assert mock_db_session.refresh.called

@pytest.mark.asyncio
async def test_delete_attendance(mock_db_session):
    """Test deleting an attendance record."""
    # Setup
    service = AttendanceService(mock_db_session)
    mock_attendance = create_mock_attendance()
    
    # Mock the get_attendance_by_id method
    service.get_attendance_by_id = AsyncMock(return_value=mock_attendance)
    
    # Test
    result = await service.delete(TEST_ATTENDANCE_ID)
    
    # Assert
    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_attendance)
    assert mock_db_session.commit.called

@pytest.mark.asyncio
async def test_get_attendance_stats(mock_db_session):
    """Test getting attendance statistics."""
    # Setup
    service = AttendanceService(mock_db_session)
    
    # Mock the query result
    mock_result = MagicMock()
    mock_result.scalar.return_value = 5  # Total count
    
    # Mock the status counts
    status_result = MagicMock()
    status_result.all.return_value = [
        ('present', 3),
        ('absent', 1),
        ('late', 1)
    ]
    
    mock_db_session.execute.side_effect = [mock_result, status_result]
    
    # Test
    result = await service.get_attendance_stats(event_id=TEST_EVENT_ID)
    
    # Assert
    assert isinstance(result, AttendanceStats)
    assert result.total == 5
    assert result.present == 3
    assert result.absent == 1
    assert result.late == 1
    assert result.percentage == 60.0  # 3/5 * 100

@pytest.mark.asyncio
async def test_get_attendance_summary(mock_db_session):
    """Test getting attendance summary by period."""
    # Setup
    service = AttendanceService(mock_db_session)
    
    # Mock the query result
    mock_result = MagicMock()
    mock_result.all.return_value = [
        ('2023-01-01', 5, 3, 1, 1, 0)  # date, total, present, absent, late, excused
    ]
    mock_db_session.execute.return_value = mock_result
    
    # Test
    result = await service.get_attendance_summary(
        organization_id=1,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31),
        period="monthly"
    )
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], AttendanceSummary)
    assert result[0].period == "monthly"
    assert result[0].total == 5
    assert result[0].present == 3
    assert result[0].absent == 1
    assert result[0].late == 1
    assert result[0].excused == 0
    assert result[0].percentage == 60.0  # 3/5 * 100
