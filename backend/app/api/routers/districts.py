from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.directories import District
from app.models.organization import Organization
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast

router = APIRouter()

@router.get("/{district_name}")
async def get_district_details(
    district_name: str, 
    start_year: int = Query(default=2022),
    end_year: int = Query(default=2025),
    db: AsyncSession = Depends(get_db)
):
    search_term = district_name.lower().replace("район", "").replace("г.", "").strip()
    
    district = (await db.execute(
        select(District).where(func.lower(District.name).like(f"%{search_term}%"))
    )).scalar_one_or_none()
    
    if not district:
        raise HTTPException(status_code=404, detail="Район не найден")
    
    orgs = (await db.execute(select(Organization).where(Organization.district_id == district.id))).scalars().all()
    org_ids = [org.id for org in orgs]
    
    if not org_ids:
        return {
            "district": {"name": district.name, "organizations_count": 0},
            "stats": {"forecast": 0.0, "fact": 0.0, "execution_percent": 0.0},
            "history": [],
            "organizations": []
        }
    
    # 1. ПЛАН: Дедупликация (берем max_id) в рамках диапазона лет
    plan_subq = (
        select(InvestmentForecast.year, InvestmentForecast.organization_id, func.max(InvestmentForecast.id).label("mid"))
        .where(
            InvestmentForecast.organization_id.in_(org_ids),
            InvestmentForecast.year >= start_year,
            InvestmentForecast.year <= end_year
        )
        .group_by(InvestmentForecast.year, InvestmentForecast.organization_id)
        .subquery()
    )
    
    plan_res = await db.execute(
        select(plan_subq.c.organization_id, plan_subq.c.year, InvestmentForecast.forecast_amount)
        .join(InvestmentForecast, InvestmentForecast.id == plan_subq.c.mid)
    )
    
    org_plans = {}
    forecast_by_year = {}
    for row in plan_res.all():
        org_id = row.organization_id
        yr = row.year
        amt = float(row.forecast_amount or 0)
        org_plans[org_id] = org_plans.get(org_id, 0.0) + amt
        forecast_by_year[yr] = forecast_by_year.get(yr, 0.0) + amt

    # 2. ФАКТ: Дедупликация (берем max_amount) в рамках диапазона лет
    fact_subq = (
        select(InvestmentFact.year, InvestmentFact.organization_id, func.max(InvestmentFact.amount).label("max_amt"))
        .where(
            InvestmentFact.organization_id.in_(org_ids),
            InvestmentFact.year >= start_year,
            InvestmentFact.year <= end_year
        )
        .group_by(InvestmentFact.year, InvestmentFact.organization_id)
        .subquery()
    )
    
    fact_res = await db.execute(select(fact_subq.c.organization_id, fact_subq.c.year, fact_subq.c.max_amt))
    
    org_facts = {}
    fact_by_year = {}
    for row in fact_res.all():
        org_id = row.organization_id
        yr = row.year
        amt = float(row.max_amt or 0)
        org_facts[org_id] = org_facts.get(org_id, 0.0) + amt
        fact_by_year[yr] = fact_by_year.get(yr, 0.0) + amt

    # 3. СБОРКА ИСТОРИИ И ОБЩЕЙ СТАТИСТИКИ (Карточка)
    all_years = sorted(set(fact_by_year.keys()) | set(forecast_by_year.keys()))
    if not all_years:
        all_years = list(range(start_year, end_year + 1))
        
    history = [
        {
            "year": y,
            "amount": round(fact_by_year.get(y, 0.0), 2),
            "forecast": round(forecast_by_year.get(y, 0.0), 2)
        }
        for y in all_years if start_year <= y <= end_year
    ]
    
    total_forecast = sum(forecast_by_year.values())
    total_fact = sum(fact_by_year.values())
    
    orgs_data = []
    for org in orgs:
        orgs_data.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "forecast": float(org_plans.get(org.id, 0)),
            "fact": float(org_facts.get(org.id, 0)),
            "execution": round((org_facts.get(org.id, 0) / org_plans.get(org.id, 1) * 100), 1) if org_plans.get(org.id, 0) > 0 else 0
        })
    
    return {
        "district": {
            "name": district.name,
            "organizations_count": len(orgs)
        },
        "stats": {
            "forecast": round(total_forecast, 2),
            "fact": round(total_fact, 2),
            "execution_percent": round((total_fact / total_forecast * 100) if total_forecast > 0 else 0, 1)
        },
        "history": history,
        "organizations": orgs_data
    }