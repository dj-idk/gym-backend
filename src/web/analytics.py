from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional
from uuid import UUID
from datetime import date

from src.data.database import get_db
from src.schema.analytics import (
    AnalyticsRead,
    UserAnalyticsRead,
    FinancialAnalyticsRead,
    ReportParameters,
    ReportFormat,
)
from src.service.analytics import analytics_service
from src.utils.auth import get_current_superuser
from src.utils.exceptions import NotFound, Forbidden

router = APIRouter(prefix="/analytics", tags=["analytics"])


# User Analytics
@router.get("/users", response_model=UserAnalyticsRead)
async def get_user_analytics(
    period: str = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user analytics. Admin only.
    """
    return await analytics_service.get_user_analytics(db, period, start_date, end_date)


@router.get("/users/retention")
async def get_user_retention_rate(
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user retention rate. Admin only.
    """
    return await analytics_service.get_user_retention_rate(db, period)


@router.get("/users/new")
async def get_new_users_by_period(
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get new users by period. Admin only.
    """
    return await analytics_service.get_new_users_by_period(db, period)


@router.get("/users/active")
async def get_active_user_count(
    current_user=Depends(get_current_superuser), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get active user count. Admin only.
    """
    return await analytics_service.get_active_user_count(db)


# Financial Analytics
@router.get("/financial", response_model=FinancialAnalyticsRead)
async def get_financial_analytics(
    period: str = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get financial analytics. Admin only.
    """
    return await analytics_service.get_financial_analytics(
        db, period, start_date, end_date
    )


@router.get("/financial/revenue")
async def get_revenue(
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get revenue by period. Admin only.
    """
    return await analytics_service.get_revenue(db, period)


@router.get("/financial/average-order")
async def get_average_order_value(
    current_user=Depends(get_current_superuser), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get average order value. Admin only.
    """
    return await analytics_service.get_average_order_value(db)


@router.get("/financial/refund-rate")
async def get_refund_rate(
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get refund rate. Admin only.
    """
    return await analytics_service.get_refund_rate(db, period)


# Service Analytics
@router.get("/services/popular")
async def get_popular_services(
    limit: int = 10,
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get most popular services. Admin only.
    """
    return await analytics_service.get_popular_services(db, limit, period)


@router.get("/services/revenue")
async def get_service_revenue(
    service_id: Optional[UUID] = None,
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get revenue by service. Admin only.
    """
    return await analytics_service.get_service_revenue(db, service_id, period)


# Coach Analytics
@router.get("/coaches/performance")
async def get_coach_performance(
    coach_id: Optional[UUID] = None,
    period: str = "month",
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get coach performance metrics. Admin only.
    """
    return await analytics_service.get_coach_performance(db, coach_id, period)


@router.get("/coaches/ratings")
async def get_coach_ratings(
    limit: int = 10,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get coach ratings. Admin only.
    """
    return await analytics_service.get_coach_ratings(db, limit)


# Reports
@router.post("/reports/generate")
async def generate_report(
    parameters: ReportParameters,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Generate a custom report. Admin only.
    """
    return await analytics_service.generate_report(db, parameters)


@router.post("/reports/export")
async def export_report(
    parameters: ReportParameters,
    format: ReportFormat = ReportFormat.PDF,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Export a report in specified format. Admin only.
    """
    return await analytics_service.export_report(db, parameters, format)


@router.get("/reports/templates")
async def list_report_templates(
    current_user=Depends(get_current_superuser), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    List available report templates. Admin only.
    """
    return await analytics_service.list_report_templates(db)


# Dashboard
@router.get("/dashboard")
async def get_dashboard_data(
    current_user=Depends(get_current_superuser), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get aggregated data for admin dashboard. Admin only.
    """
    return await analytics_service.get_dashboard_data(db)


@router.get("/comparison")
async def compare_periods(
    metric: str,
    period1: str,
    period2: str,
    current_user=Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Compare metrics between two periods. Admin only.
    """
    return await analytics_service.compare_periods(db, metric, period1, period2)
