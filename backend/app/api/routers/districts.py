# backend/app/api/routers/districts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import District, Organization, InvestmentReport

router = APIRouter()

@router.get("/{district_name}")
async def get_district_details(
    district_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить детальную статистику по конкретному району.
    """
    # Находим район
    district_res = await db.execute(
        select(District).where(District.name == district_name)
    )
    district = district_res.scalar_one_or_none()
    
    if not district:
        raise HTTPException(status_code=404, detail="Район не найден")
    
    # Получаем организации в районе
    orgs_res = await db.execute(
        select(Organization).where(Organization.district_id == district.id)
    )
    organizations = orgs_res.scalars().all()
    org_ids = [org.id for org in organizations]
    
    # Статистика по инвестициям
    current_year = 2025
    investment_stats = await db.execute(
        select(
            func.sum(InvestmentReport.forecast_annual).label('forecast'),
            func.sum(InvestmentReport.fact_annual).label('fact')
        ).where(
            InvestmentReport.organization_id.in_(org_ids),
            InvestmentReport.year == current_year
        )
    )
    stats = investment_stats.one()
    
    # История по годам
    history_res = await db.execute(
        select(
            InvestmentReport.year,
            func.sum(InvestmentReport.fact_annual)
        ).where(
            InvestmentReport.organization_id.in_(org_ids)
        ).group_by(InvestmentReport.year).order_by(InvestmentReport.year)
    )
    history = [{"year": row[0], "amount": round(row[1] or 0, 2)} for row in history_res.all()]
    
    # Список организаций с их инвестициями
    orgs_data = []
    for org in organizations:
        report_res = await db.execute(
            select(InvestmentReport).where(
                InvestmentReport.organization_id == org.id,
                InvestmentReport.year == current_year
            )
        )
        report = report_res.scalar_one_or_none()
        
        orgs_data.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "forecast": report.forecast_annual if report else 0,
            "fact": report.fact_annual if report else 0
        })
    
    return {
        "district": {
            "name": district.name,
            "organizations_count": len(organizations)
        },
        "stats": {
            "forecast": round(stats[0] or 0, 2),
            "fact": round(stats[1] or 0, 2),
            "execution_percent": round((stats[1] / stats[0] * 100) if stats[0] else 0, 1)
        },
        "history": history,
        "organizations": orgs_data
    }