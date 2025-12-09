# backend/app/api/routers/analytics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District
from typing import Optional
from datetime import date

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    year: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Статистика для дашборда:
    1. Объем инвестиций ФАКТ и ПЛАН на выбранный год.
    2. Освоение бюджета (Факт / План * 100).
    3. Количество организаций с/без инвестиций.
    """
    if year is None:
        year = date.today().year
    
    # Получаем суммы по году
    stmt = select(
        func.sum(InvestmentReport.forecast_annual).label('plan'),
        func.sum(InvestmentReport.fact_annual).label('fact'),
        func.count(InvestmentReport.id).label('total_reports')
    ).where(InvestmentReport.year == year)
    
    res = await db.execute(stmt)
    row = res.one()
    
    plan_total = float(row.plan or 0)
    fact_total = float(row.fact or 0)
    
    execution = 0
    if plan_total > 0:
        execution = round((fact_total / plan_total) * 100, 1)

    # Подсчёт организаций с/без инвестиций
    orgs_with = await db.execute(
        select(func.count(func.distinct(InvestmentReport.organization_id)))
        .where(InvestmentReport.year == year)
        .where(InvestmentReport.fact_annual > 0)
    )
    orgs_with_count = orgs_with.scalar() or 0

    total_orgs = await db.execute(select(func.count(Organization.id)))
    total_orgs_count = total_orgs.scalar() or 0

    return {
        "year": year,
        "factTotal": fact_total,
        "planTotal": plan_total,
        "forecastTotal": plan_total,
        "executionPercent": execution,
        "budgetExecution": execution,
        "orgsWithInvestments": orgs_with_count,
        "orgsWithoutInvestments": total_orgs_count - orgs_with_count
    }


@router.get("/stats")
async def get_dashboard_stats_legacy(db: AsyncSession = Depends(get_db)):
    """
    Legacy endpoint для обратной совместимости
    """
    return await get_dashboard_stats(year=date.today().year, db=db)


@router.get("/map")
async def get_map_data(
    year: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Данные для раскраски карты районов.
    """
    if year is None:
        year = date.today().year
        
    stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual).label('total')
    ).select_from(Organization)\
     .join(District, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == year)\
     .group_by(District.name)

    res = await db.execute(stmt)
    data = [{"name": row[0], "value": float(row[1] or 0)} for row in res.all()]
    return data


@router.get("/trends")
async def get_analytics_trends(
    year: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    1. История (динамика по годам).
    2. Топ-5 Районов.
    3. Прогноз.
    """
    if year is None:
        year = date.today().year
    
    # 1. ИСТОРИЯ ПО ГОДАМ
    hist_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.fact_annual).label('fact'),
        func.sum(InvestmentReport.forecast_annual).label('forecast')
    ).group_by(InvestmentReport.year).order_by(InvestmentReport.year)
    
    hist_res = await db.execute(hist_stmt)
    history = [
        {
            "year": row[0], 
            "amount": float(row[1] or 0),
            "forecast": float(row[2] or 0)
        } 
        for row in hist_res.all()
    ]

    # 2. РЕЙТИНГ ТОП-5 РАЙОНОВ
    top_stmt = select(
        District.name,
        func.sum(InvestmentReport.fact_annual).label("total")
    ).select_from(Organization)\
     .join(District, Organization.district_id == District.id)\
     .join(InvestmentReport, InvestmentReport.organization_id == Organization.id)\
     .where(InvestmentReport.year == year)\
     .group_by(District.name)\
     .order_by(desc("total"))\
     .limit(5)
    
    top_res = await db.execute(top_stmt)
    rating = [{"name": row[0], "value": float(row[1] or 0)} for row in top_res.all()]

    # 3. ПРОГНОЗ
    forecast_stmt = select(
        InvestmentReport.year,
        func.sum(InvestmentReport.forecast_annual).label("forecast")
    ).where(InvestmentReport.year >= year)\
     .group_by(InvestmentReport.year)\
     .order_by(InvestmentReport.year)
    
    forecast_res = await db.execute(forecast_stmt)
    forecast_data = [{"year": row[0], "amount": float(row[1] or 0)} for row in forecast_res.all()]

    return {
        "history": history,
        "rating": rating,
        "forecast": forecast_data
    }


@router.get("/quarters")
async def get_quarterly_data(
    year: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Данные по кварталам для выбранного года.
    """
    if year is None:
        year = date.today().year

    # Получаем суммы по кварталам
    stmt = select(
        func.sum(InvestmentReport.fact_q1).label('q1_fact'),
        func.sum(InvestmentReport.fact_q2).label('q2_fact'),
        func.sum(InvestmentReport.fact_q3).label('q3_fact'),
        func.sum(InvestmentReport.fact_q4).label('q4_fact'),
        func.sum(InvestmentReport.forecast_annual).label('plan_total')
    ).where(InvestmentReport.year == year)
    
    res = await db.execute(stmt)
    row = res.one()
    
    plan_total = float(row.plan_total or 0)
    plan_per_quarter = plan_total / 4 if plan_total > 0 else 0
    
    return [
        {"quarter": 1, "fact": float(row.q1_fact or 0), "plan": plan_per_quarter},
        {"quarter": 2, "fact": float(row.q2_fact or 0), "plan": plan_per_quarter},
        {"quarter": 3, "fact": float(row.q3_fact or 0), "plan": plan_per_quarter},
        {"quarter": 4, "fact": float(row.q4_fact or 0), "plan": plan_per_quarter}
    ]


@router.post("/calculate/clustering")
async def calculate_clusters():
    """
    Запуск кластеризации организаций (заглушка).
    """
    return {"status": "success", "message": "Clustering updated"}