from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.organization import Organization
from app.models.directories import District 
from app.services.pdf_generator import generate_analytics_pdf
from datetime import datetime

router = APIRouter()

@router.get("/analytics-pdf")
async def export_analytics_pdf(
    start_year: int = Query(...),
    end_year: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Годовые данные
    facts_query = select(
        InvestmentFact.year, func.sum(InvestmentFact.amount).label("fact")
    ).where(InvestmentFact.year >= start_year, InvestmentFact.year <= end_year).group_by(InvestmentFact.year)
    facts_result = (await db.execute(facts_query)).all()
    fact_dict = {row.year: float(row.fact) for row in facts_result}

    subq = select(
        InvestmentForecast.organization_id, InvestmentForecast.year, func.max(InvestmentForecast.id).label("max_id")
    ).where(InvestmentForecast.year >= start_year, InvestmentForecast.year <= end_year).group_by(InvestmentForecast.organization_id, InvestmentForecast.year).subquery()
    
    plans_query = select(
        subq.c.year, func.sum(InvestmentForecast.forecast_amount).label("plan")
    ).join(InvestmentForecast, InvestmentForecast.id == subq.c.max_id).group_by(subq.c.year)
    plans_result = (await db.execute(plans_query)).all()
    plan_dict = {row.year: float(row.plan) for row in plans_result}

    yearly_data = []
    for y in range(start_year, end_year + 1):
        yearly_data.append({
            "year": y,
            "fact": fact_dict.get(y, 0),
            "plan": plan_dict.get(y, 0)
        })

    # 2. Количество организаций
    org_subq = select(
        InvestmentFact.organization_id, func.max(InvestmentFact.amount).label('max_amount')
    ).where(InvestmentFact.year >= start_year, InvestmentFact.year <= end_year).group_by(InvestmentFact.organization_id).subquery()
    
    orgs_query = select(func.count(func.distinct(org_subq.c.organization_id))).where(org_subq.c.max_amount > 0)
    total_orgs = (await db.execute(orgs_query)).scalar() or 0

    # 3. Топ-5 районов (ИСПРАВЛЕНО: используем District)
    dist_subq = select(
        InvestmentFact.organization_id, func.max(InvestmentFact.amount).label('max_amount')
    ).where(InvestmentFact.year >= start_year, InvestmentFact.year <= end_year).group_by(InvestmentFact.organization_id).subquery()
    
    dist_query = select(
            func.coalesce(District.name, 'Не распределено').label('name'),
            func.sum(dist_subq.c.max_amount).label('total')
        ).select_from(
            dist_subq  # <--- Явно указываем стартовую точку
        ).join(
            Organization, dist_subq.c.organization_id == Organization.id
        ).outerjoin(
            District, Organization.district_id == District.id
        ).group_by(District.name).order_by(desc('total')).limit(5)
    
    dist_result = (await db.execute(dist_query)).all()
    top_districts = [{"name": r.name, "value": float(r.total)} for r in dist_result]

    # 4. Кварталы 
    q_query = select(
        InvestmentFact.quarter, func.sum(InvestmentFact.amount).label("fact")
    ).where(InvestmentFact.year >= start_year, InvestmentFact.year <= end_year).group_by(InvestmentFact.quarter).order_by(InvestmentFact.quarter)
    q_result = (await db.execute(q_query)).all()
    quarters = [{"quarter": r.quarter, "fact": float(r.fact)} for r in q_result]

    # Собираем все данные
    pdf_data = {
        "start_year": start_year,
        "end_year": end_year,
        "yearly_data": yearly_data,
        "total_orgs": total_orgs,
        "top_districts": top_districts,
        "quarters": quarters
    }

    pdf_buffer = generate_analytics_pdf(pdf_data)
    filename = f"Analytics_Report_{start_year}_{end_year}.pdf"

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )