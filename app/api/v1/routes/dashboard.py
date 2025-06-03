from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, List, Optional, Any
from datetime import datetime
from pymongo.database import Database

from app.core.security import get_current_active_user
from app.models.user import UserInDB # Assuming UserInDB is the correct model for current_user
from app.services.dashboard_service import DashboardService
from app.db.mongodb import get_db
from app.schemas.dashboard import (
    DashboardSummary,
    DashboardEventInfo,
    DashboardMetric,
    DashboardTrends,
    DashboardNotification,
    DashboardGenericResponse
)

router = APIRouter()

# TODO: Implement organization_id filtering in service methods if required by business logic.
# The organization_id parameter is kept in route signatures for potential future use.

@router.get("/dashboard", tags=["dashboard"], response_model=DashboardSummary) # Example, might need a more comprehensive model
def get_dashboard(
    organization_id: Optional[str] = None,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard overview. For now, returns the summary.
    """
    service = DashboardService(db)
    # This endpoint might combine multiple pieces of data in the future.
    # For now, it returns the same as /dashboard/summary
    return service.get_summary_data()

@router.get("/dashboard/stats", tags=["dashboard"], response_model=DashboardGenericResponse) # Placeholder response
def get_dashboard_stats(
    organization_id: Optional[str] = None,
    period: str = Query("month", enum=["day", "week", "month", "year"]),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard statistics with period-based filtering. (Placeholder)
    """
    # service = DashboardService(db)
    # data = service.get_stats_data(organization_id=organization_id, period=period)
    # return data
    return DashboardGenericResponse(message="Statistics endpoint not fully implemented.")

@router.get("/dashboard/attendance", tags=["dashboard"], response_model=DashboardGenericResponse) # Placeholder response
def get_dashboard_attendance(
    organization_id: Optional[str] = None,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard attendance records with date filtering. (Placeholder)
    """
    # service = DashboardService(db)
    # data = service.get_attendance_data(organization_id=organization_id, start_date=start_date, end_date=end_date)
    # return data
    return DashboardGenericResponse(message="Attendance endpoint not fully implemented.")

@router.get("/dashboard/events", response_model=List[DashboardEventInfo], tags=["dashboard"])
def get_dashboard_events(
    organization_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard events with pagination.
    """
    service = DashboardService(db)
    events = service.get_dashboard_events_data(limit=limit)
    # Add skip and organization_id filtering in service if needed
    return events

@router.get("/dashboard/meetings", response_model=List[DashboardEventInfo], tags=["dashboard"])
def get_dashboard_meetings(
    organization_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard meetings with pagination.
    """
    service = DashboardService(db)
    meetings = service.get_dashboard_meetings_data(limit=limit)
    # Add skip and organization_id filtering in service if needed
    return meetings

@router.get("/dashboard/summary", response_model=DashboardSummary, tags=["dashboard"])
def get_dashboard_summary(
    organization_id: Optional[str] = None,
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard summary statistics.
    """
    service = DashboardService(db)
    summary = service.get_summary_data()
    return summary

@router.get("/dashboard/trends", response_model=DashboardTrends, tags=["dashboard"])
def get_dashboard_trends(
    organization_id: Optional[str] = None,
    period: str = Query("month", enum=["day", "week", "month", "year"]),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard trend data.
    """
    service = DashboardService(db)
    trends = service.get_dashboard_trends_data()
    # Add period and organization_id filtering in service if needed
    return trends

@router.get("/dashboard/notifications", response_model=List[DashboardNotification], tags=["dashboard"])
def get_dashboard_notifications(
    organization_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard notifications with pagination.
    """
    service = DashboardService(db)
    notifications = service.get_dashboard_notifications_data(limit=limit)
    # Add skip and organization_id filtering in service if needed
    return notifications

@router.get("/dashboard/reports", response_model=DashboardGenericResponse, tags=["dashboard"])
def get_dashboard_reports(
    organization_id: Optional[str] = None,
    report_type: str = Query("attendance", enum=["attendance", "events", "meetings"]),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard reports by type.
    """
    service = DashboardService(db)
    reports = service.get_dashboard_reports_data()
    # Add report_type and organization_id filtering in service if needed
    return reports

@router.get("/dashboard/activities", response_model=DashboardGenericResponse, tags=["dashboard"])
def get_dashboard_activities(
    organization_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard activities with pagination.
    """
    service = DashboardService(db)
    activities = service.get_dashboard_activities_data()
    # Add skip, limit, and organization_id filtering in service if needed
    return activities

@router.get("/dashboard/metrics", response_model=List[DashboardMetric], tags=["dashboard"])
def get_dashboard_metrics(
    organization_id: Optional[str] = None,
    metric_type: str = Query("all", enum=["all", "attendance", "engagement", "growth"]),
    db: Database = Depends(get_db),
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get dashboard metrics by type.
    """
    service = DashboardService(db)
    metrics = service.get_dashboard_metrics_data()
    # Add metric_type and organization_id filtering in service if needed
    return metrics
