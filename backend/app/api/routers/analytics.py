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
    
    data_quality = round((reports_count / org_count) * 100, 1) if org_count > 0 else 0

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
    year: int = Query(default=None),
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

@router.get("/district/{district_name}")
async def get_district_stats(
    district_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Статистика по конкретному району"""
    from sqlalchemy.orm import selectinload
    
    # Находим район
    district_res = await db.execute(
        select(District).where(District.name == district_name)
    )
    district = district_res.scalar_one_or_none()
    
    if not district:
        return {
            "name": district_name,
            "organizationCount": 0,
            "totalFact": 0,
            "totalForecast": 0,
            "byYear": [],
            "error": "Район не найден в базе данных"
        }
    
    # Количество организаций в районе
    org_count_res = await db.execute(
        select(func.count(Organization.id))
        .where(Organization.district_id == district.id)
    )
    org_count = org_count_res.scalar() or 0
    
    # Общая сумма инвестиций
    total_res = await db.execute(
        select(
            func.sum(InvestmentReport.fact_annual),
            func.sum(InvestmentReport.forecast_annual)
        )
        .join(Organization, InvestmentReport.organization_id == Organization.id)
        .where(Organization.district_id == district.id)
    )
    totals = total_res.one()
    
    # Инвестиции по годам
    by_year_res = await db.execute(
        select(
            InvestmentReport.year,
            func.sum(InvestmentReport.fact_annual)
        )
        .join(Organization, InvestmentReport.organization_id == Organization.id)
        .where(Organization.district_id == district.id)
        .group_by(InvestmentReport.year)
        .order_by(InvestmentReport.year)
    )
    by_year = [{"year": r[0], "amount": r[1] or 0} for r in by_year_res.all()]
    
    return {
        "name": district_name,
        "organizationCount": org_count,
        "totalFact": totals[0] or 0,
        "totalForecast": totals[1] or 0,
        "byYear": by_year
    }

@router.get("/trends")
async def get_analytics_trends(db: AsyncSession = Depends(get_db)):
    # 1. ИСТОРИЯ - все годы
    hist_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.fact_annual)
    ).group_by(InvestmentReport.year).order_by(InvestmentReport.year)
    
    hist_res = await db.execute(hist_stmt)
    history = [{"year": row[0], "amount": row[1] or 0} for row in hist_res.all()]

    # 2. РЕЙТИНГ ТОП-3 ЗА ВСЕ ВРЕМЯ (не только 2025!)
    top_stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual).label("total")
    ).join(Organization, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .group_by(District.name)\
     .order_by(desc("total"))\
     .limit(3)
    
    top_res = await db.execute(top_stmt)
    rating = [{"name": row[0], "value": row[1] or 0} for row in top_res.all()]

    # 3. ПРОГНОЗ - берем forecast_annual и строим линию
    forecast_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.forecast_annual).label("forecast")
    ).group_by(InvestmentReport.year)\
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