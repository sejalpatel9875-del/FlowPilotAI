from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import UserModel
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve 100% real database metrics for 9 summary cards and 11 tracked dimensions."""
    data = await AnalyticsService.get_analytics_overview(user.id, db)
    return data


@router.get("/charts")
async def get_analytics_chart_data(
    user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve real database dataset structures for 5 UI charts."""
    charts = await AnalyticsService.get_chart_data(user.id, db)
    return charts
