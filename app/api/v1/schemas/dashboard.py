from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Example schema for a summary item
class DashboardSummaryItem(BaseModel):
    title: str
    value: Any
    unit: Optional[str] = None

class DashboardSummary(BaseModel):
    total_users: int
    total_events: int
    upcoming_events_count: int
    # Add more summary fields as needed

# Example schema for a simplified event listing for the dashboard
class DashboardEventInfo(BaseModel):
    id: str
    name: str
    event_date: datetime
    location: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# Example schema for a generic metric
class DashboardMetric(BaseModel):
    name: str
    value: Any
    details: Optional[Dict[str, Any]] = None

# Example schema for trend data (e.g., for charts)
class DashboardTrendPoint(BaseModel):
    timestamp: datetime
    value: float

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class DashboardTrends(BaseModel):
    user_registration_trend: List[DashboardTrendPoint]
    event_creation_trend: List[DashboardTrendPoint]

# Placeholder for notifications, reports, activities if they have specific structures
class DashboardNotification(BaseModel):
    id: str
    message: str
    created_at: datetime
    is_read: bool = False

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

# A general schema for routes that might return a list of generic items or a message
class DashboardGenericResponse(BaseModel):
    message: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
