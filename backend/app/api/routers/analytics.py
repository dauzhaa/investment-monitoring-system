from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.organization import Organization
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.directories import District
from typing import Optional
from datetime import date

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    # 1. Считаем ФАКТ за период (группируем по организации и году, чтобы избежать дублей)
    fact_subq = (
        select(InvestmentFact.organization_id, InvestmentFact.year, func.max(InvestmentFact.amount).label("max_amount"))
        .where(InvestmentFact.year >= start_year)
        .where(InvestmentFact.year <= end_year)
        .group_by(InvestmentFact.organization_id, InvestmentFact.year)
        .subquery()
    )
    fact_res = await db.execute(select(func.sum(fact_subq.c.max_amount)))
    fact_total = float(fact_res.scalar() or 0)

    # 2. Считаем ПЛАН за период
    plan_subq = (
        select(InvestmentForecast.organization_id, InvestmentForecast.year, func.max(InvestmentForecast.id).label("max_id"))
        .where(InvestmentForecast.year >= start_year)
        .where(InvestmentForecast.year <= end_year)
        .group_by(InvestmentForecast.organization_id, InvestmentForecast.year)
        .subquery()
    )
    plan_stmt = select(func.sum(InvestmentForecast.forecast_amount)).join(
        plan_subq, InvestmentForecast.id == plan_subq.c.max_id
    )
    plan_res = await db.execute(plan_stmt)
    plan_total = float(plan_res.scalar() or 0)

    # 3. Выполнение
    execution = round((fact_total / plan_total) * 100, 1) if plan_total > 0 else 0

    # 4. Организации с инвестициями (считаем уникальные ID за весь период)
    orgs_with_res = await db.execute(
        select(func.count(func.distinct(fact_subq.c.organization_id)))
        .where(fact_subq.c.max_amount > 0)
    )
    orgs_with_count = orgs_with_res.scalar() or 0

    total_orgs_res = await db.execute(select(func.count(Organization.id)))
    total_orgs_count = total_orgs_res.scalar() or 0

    return {
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
    return await get_dashboard_stats(start_year=date.today().year, end_year=date.today().year, db=db)


@router.get("/map")
async def get_map_data(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    fact_subq = (
        select(InvestmentFact.organization_id, InvestmentFact.year, func.max(InvestmentFact.amount).label("max_amount"))
        .where(InvestmentFact.year >= start_year)
        .where(InvestmentFact.year <= end_year)
        .group_by(InvestmentFact.organization_id, InvestmentFact.year)
        .subquery()
    )

    stmt = select(
        func.coalesce(District.name, 'Не распределено').label('district_name'),
        func.sum(fact_subq.c.max_amount).label('total')
    ).select_from(Organization)\
     .join(fact_subq, fact_subq.c.organization_id == Organization.id)\
     .outerjoin(District, Organization.district_id == District.id)\
     .group_by(District.name)

    res = await db.execute(stmt)
    return [{"name": row.district_name, "value": float(row.total or 0)} for row in res.all()]


@router.get("/trends")
async def get_analytics_trends(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    years_res = await db.execute(select(func.distinct(InvestmentFact.year)))
    all_years = sorted([y[0] for y in years_res.all() if y[0] is not None])
    
    history = []
    forecast_data = []
    
    for y in all_years:
        f_subq = select(func.max(InvestmentFact.amount).label("max_amount")).where(InvestmentFact.year == y).group_by(InvestmentFact.organization_id).subquery()
        f_res = await db.execute(select(func.sum(f_subq.c.max_amount)))
        fact_sum = float(f_res.scalar() or 0)
        
        p_subq = select(func.max(InvestmentForecast.id).label("mid")).where(InvestmentForecast.year == y).group_by(InvestmentForecast.organization_id).subquery()
        p_res = await db.execute(select(func.sum(InvestmentForecast.forecast_amount)).join(p_subq, InvestmentForecast.id == p_subq.c.mid))
        plan_sum = float(p_res.scalar() or 0)
        
        history.append({"year": y, "amount": fact_sum, "forecast": plan_sum})
        if y >= start_year:
            forecast_data.append({"year": y, "amount": plan_sum})

    map_data = await get_map_data(start_year, end_year, db)
    rating = sorted(map_data, key=lambda x: x['value'], reverse=True)[:5]

    return {
        "history": history,
        "rating": rating,
        "forecast": forecast_data
    }


@router.get("/quarters")
async def get_quarterly_data(
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2026),
    db: AsyncSession = Depends(get_db)
):
    quarters_data = []
    
    # План за период
    plan_subq = select(InvestmentForecast.organization_id, InvestmentForecast.year, func.max(InvestmentForecast.id).label("mid")).where(
        InvestmentForecast.year >= start_year, InvestmentForecast.year <= end_year
    ).group_by(InvestmentForecast.organization_id, InvestmentForecast.year).subquery()
    
    plan_res = await db.execute(select(func.sum(InvestmentForecast.forecast_amount)).join(plan_subq, InvestmentForecast.id == plan_subq.c.mid))
    plan_total = float(plan_res.scalar() or 0)
    plan_per_quarter = plan_total / 4 if plan_total > 0 else 0

    for q in [1, 2, 3, 4]:
        stmt = select(func.sum(InvestmentFact.amount)).where(
            InvestmentFact.year >= start_year,
            InvestmentFact.year <= end_year,
            InvestmentFact.quarter == q
        )
        res = await db.execute(stmt)
        fact_sum = float(res.scalar() or 0)
        
        quarters_data.append({"quarter": q, "fact": fact_sum, "plan": plan_per_quarter})
        
    return quarters_data