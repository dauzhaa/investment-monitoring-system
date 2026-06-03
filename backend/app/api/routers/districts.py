from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.directories import District
from app.models.organization import Organization
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from datetime import date

router = APIRouter()

@router.get("/{district_name}")
async def get_district_details(district_name: str, db: AsyncSession = Depends(get_db)):
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
        
    # ИЗМЕНЕНО: Динамический поиск последнего года с данными
    latest_year_res = await db.execute(
        select(func.max(InvestmentFact.year))
        .where(InvestmentFact.organization_id.in_(org_ids))
    )
    current_year = latest_year_res.scalar()
    if not current_year:
        current_year = date.today().year
    
    # План (за current_year — для верхних карточек stats и таблицы организаций)
    plan_subq = select(InvestmentForecast.organization_id, func.max(InvestmentForecast.id).label("mid")).where(
        InvestmentForecast.organization_id.in_(org_ids), InvestmentForecast.year == current_year
    ).group_by(InvestmentForecast.organization_id).subquery()
    
    plan_res = await db.execute(
        select(InvestmentForecast.organization_id, InvestmentForecast.forecast_amount)
        .join(plan_subq, InvestmentForecast.id == plan_subq.c.mid)
    )
    plans = dict(plan_res.all())
    
    # Факт (за вычисленный current_year)
    fact_res = await db.execute(
        select(InvestmentFact.organization_id, func.max(InvestmentFact.amount))
        .where(InvestmentFact.organization_id.in_(org_ids), InvestmentFact.year == current_year)
        .group_by(InvestmentFact.organization_id)
    )
    facts = dict(fact_res.all())
    
    # --- История ФАКТОВ по годам ---
    hist_subq = select(InvestmentFact.year, InvestmentFact.organization_id, func.max(InvestmentFact.amount).label("max_amt")).where(
        InvestmentFact.organization_id.in_(org_ids)
    ).group_by(InvestmentFact.year, InvestmentFact.organization_id).subquery()
    
    hist_res = await db.execute(
        select(hist_subq.c.year, func.sum(hist_subq.c.max_amt))
        .group_by(hist_subq.c.year).order_by(hist_subq.c.year)
    )
    fact_by_year = {row[0]: round(float(row[1] or 0), 2) for row in hist_res.all()}

    # --- НОВОЕ: История ПЛАНА по годам ---
    # последний прогноз каждой организации за каждый год (max id), затем сумма по году
    plan_hist_subq = select(
        InvestmentForecast.year,
        InvestmentForecast.organization_id,
        func.max(InvestmentForecast.id).label("mid"),
    ).where(
        InvestmentForecast.organization_id.in_(org_ids)
    ).group_by(InvestmentForecast.year, InvestmentForecast.organization_id).subquery()

    plan_hist_res = await db.execute(
        select(plan_hist_subq.c.year, func.sum(InvestmentForecast.forecast_amount))
        .join(plan_hist_subq, InvestmentForecast.id == plan_hist_subq.c.mid)
        .group_by(plan_hist_subq.c.year)
    )
    forecast_by_year = {row[0]: round(float(row[1] or 0), 2) for row in plan_hist_res.all()}

    # --- СЛИЯНИЕ факта и плана по годам ---
    all_years = sorted(set(fact_by_year) | set(forecast_by_year))
    history = [
        {
            "year": y,
            "amount": fact_by_year.get(y, 0.0),
            "forecast": forecast_by_year.get(y, 0.0),   # ← фронт теперь видит «План»
        }
        for y in all_years
    ]
    
    total_forecast = sum(plans.values())
    total_fact = sum(facts.values())
    
    orgs_data = []
    for org in orgs:
        orgs_data.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "forecast": float(plans.get(org.id, 0)),
            "fact": float(facts.get(org.id, 0))
        })
    
    return {
        "district": {
            "name": district.name,
            "organizations_count": len(orgs)
        },
        "stats": {
            "forecast": round(total_forecast, 2),
            "fact": round(total_fact, 2),
            "execution_percent": round((total_fact / total_forecast * 100) if total_forecast else 0, 1)
        },
        "history": history,
        "organizations": orgs_data
    }