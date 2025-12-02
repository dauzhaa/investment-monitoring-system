# backend/app/api/routers/analytics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    year: int = Query(default=None, description="Год для статистики"),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
    
    stmt = select(
        func.sum(InvestmentReport.forecast_annual),
        func.sum(InvestmentReport.fact_annual)
    ).where(InvestmentReport.year == year)
    
    res = await db.execute(stmt)
    row = res.one()
    
    forecast_total = row[0] or 0
    fact_total = row[1] or 0
    
    execution = 0
    if forecast_total > 0:
        execution = (fact_total / forecast_total) * 100

    org_count_res = await db.execute(select(func.count(Organization.id)))
    org_count = org_count_res.scalar() or 0

    reports_count_res = await db.execute(
        select(func.count(func.distinct(InvestmentReport.organization_id)))
        .where(InvestmentReport.year == year)
    )
    reports_count = reports_count_res.scalar() or 0
    
    data_quality = 0
    if org_count > 0:
        data_quality = round((reports_count / org_count) * 100, 1)

    return {
        "currentYearTotal": forecast_total,
        "factTotal": fact_total,
        "forecastTotal": forecast_total,
        "budgetExecution": round(execution, 1),
        "organizationCount": org_count,
        "dataQuality": data_quality
    }

@router.get("/map")
async def get_map_data(
    year: int = Query(default=None, description="Год для карты"),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
        
    stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual)
    ).join(Organization, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == year)\
     .group_by(District.name)

    res = await db.execute(stmt)
    data = [{"name": row[0], "value": row[1] or 0} for row in res.all()]
    return data

@router.get("/trends")
async def get_analytics_trends(db: AsyncSession = Depends(get_db)):
    current_year = datetime.now().year
    
    hist_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.fact_annual)
    ).group_by(InvestmentReport.year).order_by(InvestmentReport.year)
    
    hist_res = await db.execute(hist_stmt)
    history = [{"year": row[0], "amount": row[1] or 0} for row in hist_res.all()]

    top_stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual).label("total")
    ).join(Organization, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == current_year)\
     .group_by(District.name)\
     .order_by(desc("total"))\
     .limit(3)
    
    top_res = await db.execute(top_stmt)
    rating = [{"name": row[0], "value": row[1] or 0} for row in top_res.all()]

    forecast_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.forecast_annual).label("forecast")
    ).where(InvestmentReport.year >= current_year)\
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