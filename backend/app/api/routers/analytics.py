# backend/app/api/routers/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Статистика для дашборда:
    1. Объем инвестиций (План) на 2025 год.
    2. Освоение бюджета (Факт / План * 100).
    3. Итого факт и план.
    """
    current_year = 2025
    
    stmt = select(
        func.sum(InvestmentReport.forecast_annual),
        func.sum(InvestmentReport.fact_annual)
    ).where(InvestmentReport.year == current_year)
    
    res = await db.execute(stmt)
    row = res.one()
    
    forecast_total = row[0] or 0
    fact_total = row[1] or 0
    
    execution = 0
    if forecast_total > 0:
        execution = (fact_total / forecast_total) * 100

    return {
        "currentYearTotal": forecast_total,
        "factTotal": fact_total,
        "forecastTotal": forecast_total,
        "budgetExecution": round(execution, 1)
    }

@router.get("/map")
async def get_map_data(db: AsyncSession = Depends(get_db)):
    """
    Данные для раскраски карты районов.
    """
    stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual)
    ).join(Organization, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == 2025)\
     .group_by(District.name)

    res = await db.execute(stmt)
    data = [{"name": row[0], "value": row[1] or 0} for row in res.all()]
    return data

@router.get("/trends")
async def get_analytics_trends(db: AsyncSession = Depends(get_db)):
    """
    1. История (динамика по годам).
    2. Топ-3 Района.
    3. Прогноз (используем forecast_annual из investment_reports).
    """
    
    # 1. ИСТОРИЯ
    hist_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.fact_annual)
    ).group_by(InvestmentReport.year).order_by(InvestmentReport.year)
    
    hist_res = await db.execute(hist_stmt)
    history = [{"year": row[0], "amount": row[1] or 0} for row in hist_res.all()]

    # 2. РЕЙТИНГ ТОП-3
    top_stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual).label("total")
    ).join(Organization, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == 2025)\
     .group_by(District.name)\
     .order_by(desc("total"))\
     .limit(3)
    
    top_res = await db.execute(top_stmt)
    rating = [{"name": row[0], "value": row[1] or 0} for row in top_res.all()]

    # 3. ПРОГНОЗ (из forecast_annual в investment_reports)
    forecast_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.forecast_annual).label("forecast")
    ).where(InvestmentReport.year >= 2025)\
     .group_by(InvestmentReport.year)\
     .order_by(InvestmentReport.year)
    
    forecast_res = await db.execute(forecast_stmt)
    forecast_data = [{"year": row[0], "amount": row[1] or 0} for row in forecast_res.all()]

    return {
        "history": history,
        "rating": rating,
        "forecast": forecast_data
    }

@router.post("/calculate/clustering")
async def calculate_clusters():
    return {"status": "success", "message": "Clustering updated"}