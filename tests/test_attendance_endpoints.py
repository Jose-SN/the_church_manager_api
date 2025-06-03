import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User as UserModel
from app.models.attendance import Attendance as AttendanceModel
from app.schemas.attendance import (
    Attendance, 
    AttendanceCreate, 
    AttendanceUpdate,
    AttendanceStatus,
    AttendanceStats
)

# Test client
client = TestClient(app)


# Test data
TEST_USER_ID = 1
TEST_EVENT_ID = 1
TEST_ATTENDANCE_ID = 1

def create_mock_user(is_superuser: bool = False):
    """Create a mock user object."""
    user = UserModel(
        id=TEST_USER_ID,
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        is_superuser=is_superuser
    )
    return user

def create_mock_attendance(**kwargs):
    """Create a mock attendance object."""
    defaults = {
        'id': TEST_ATTENDANCE_ID,
        'user_id': TEST_USER_ID,
        'event_id': TEST_EVENT_ID,
        'status': AttendanceStatus.PRESENT.value,
        'recorded_by': 1,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    defaults.update(kwargs)
    return AttendanceModel(**defaults)

# Authentication fixtures
@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer testtoken"}

# Test cases
class TestAttendanceEndpoints:
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_create_attendance(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        attendance_data = {
            "user_id": TEST_USER_ID,
            "event_id": TEST_EVENT_ID,
            "status": "present"
        }
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_by_user_and_event.return_value = None
            mock_attendance = create_mock_attendance(**attendance_data)
            mock_service.return_value.create.return_value = mock_attendance
            
            # Test
            response = client.post(
                "/api/v1/attendance/",
                json=attendance_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["user_id"] == TEST_USER_ID
            assert data["event_id"] == TEST_EVENT_ID
            assert data["status"] == "present"
    
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_get_attendance(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        mock_attendance = create_mock_attendance()
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_by_id.return_value = mock_attendance
            
            # Test
            response = client.get(
                f"/api/v1/attendance/{TEST_ATTENDANCE_ID}",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == TEST_ATTENDANCE_ID
            assert data["user_id"] == TEST_USER_ID
    
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_list_attendance(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        mock_attendances = [
            create_mock_attendance(id=1, status="present"),
            create_mock_attendance(id=2, status="absent"),
        ]
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.list_attendance.return_value = mock_attendances
            
            # Test
            response = client.get(
                "/api/v1/attendance/",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == 1
            assert data[1]["id"] == 2
    
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_update_attendance(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        update_data = {"status": "absent"}
        updated_attendance = create_mock_attendance(status="absent")
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_by_id.return_value = create_mock_attendance()
            mock_service.return_value.update.return_value = updated_attendance
            
            # Test
            response = client.put(
                f"/api/v1/attendance/{TEST_ATTENDANCE_ID}",
                json=update_data,
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "absent"
    
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_delete_attendance(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_by_id.return_value = create_mock_attendance()
            mock_service.return_value.delete.return_value = True
            
            # Test
            response = client.delete(
                f"/api/v1/attendance/{TEST_ATTENDANCE_ID}",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_204_NO_CONTENT
    
    @patch("app.api.deps.get_current_active_user")
    @patch("app.api.deps.get_db")
    async def test_get_event_attendance_stats(self, mock_get_db, mock_current_user, auth_headers):
        # Setup
        mock_user = create_mock_user()
        mock_current_user.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        stats = AttendanceStats(
            total=5,
            present=3,
            absent=1,
            late=1,
            excused=0,
            percentage=60.0
        )
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_stats.return_value = stats
            
            # Test
            response = client.get(
                f"/api/v1/attendance/event/{TEST_EVENT_ID}/stats",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 5
            assert data["present"] == 3
            assert data["percentage"] == 60.0
    
    @patch("app.api.deps.get_current_active_superuser")
    @patch("app.api.deps.get_db")
    async def test_get_attendance_summary(self, mock_get_db, mock_current_superuser, auth_headers):
        # Setup
        mock_user = create_mock_user(is_superuser=True)
        mock_current_superuser.return_value = mock_user
        
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        
        # Mock the service
        with patch("app.services.attendance_service.AttendanceService") as mock_service:
            mock_service.return_value.get_attendance_summary.return_value = [
                {
                    "period": "daily",
                    "date": "2023-01-01",
                    "total": 5,
                    "present": 3,
                    "absent": 1,
                    "late": 1,
                    "excused": 0,
                    "percentage": 60.0
                }
            ]
            
            # Test
            response = client.get(
                "/api/v1/attendance/summary/?organization_id=1&start_date=2023-01-01&end_date=2023-01-31&period=daily",
                headers=auth_headers
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["period"] == "daily"
            assert data[0]["total"] == 5
