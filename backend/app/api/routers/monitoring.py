from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.organization import Organization
from app.models.directories import District
from app.models.report_submission import ReportSubmission
from app.models.investment_forecast import InvestmentForecast
from typing import Optional
from datetime import date
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_monitoring_status(
    year: int = Query(default=None), 
    quarter: int = Query(default=1),
    districts: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = date.today().year
    
    # 1. Получаем организации
    stmt = select(Organization).options(
        selectinload(Organization.district)
    ).order_by(Organization.name)
    
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    orgs_result = await db.execute(stmt)
    all_orgs = orgs_result.scalars().all()
    
    # 2. Получаем статусы сдачи
    subm_stmt = select(ReportSubmission).where(
        ReportSubmission.year == year,
        ReportSubmission.quarter == quarter
    )
    subm_result = await db.execute(subm_stmt)
    submissions = {s.organization_id: s for s in subm_result.scalars().all()}
    
    # 3. Получаем прогнозы (чтобы понять, запланировано ли вообще)
    forecast_stmt = select(InvestmentForecast.organization_id, func.max(InvestmentForecast.forecast_amount)).where(
        InvestmentForecast.year == year
    ).group_by(InvestmentForecast.organization_id)
    forecast_result = await db.execute(forecast_stmt)
    forecasts = dict(forecast_result.all())
    
    result = []
    submitted_count = 0
    overdue_count = 0
    not_planned_count = 0
    
    for org in all_orgs:
        subm = submissions.get(org.id)
        has_forecast = forecasts.get(org.id, 0) > 0
        
        status = "not_planned"
        if subm:
            status = subm.status  # 'submitted', 'pending', 'overdue'
            if status == "pending" and not has_forecast:
                status = "not_planned"
        else:
            if has_forecast:
                status = "overdue" # Если план есть, а записи о сдаче нет
            else:
                status = "not_planned"
                
        if status == 'submitted': submitted_count += 1
        elif status == 'overdue': overdue_count += 1
        elif status in ('not_planned', 'pending'): not_planned_count += 1
        
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "district": org.district.name if org.district else "Не указан",
            "email": org.contact_email,
            "status": status,
            "is_smp": org.is_smp
        })
    
    total = len(all_orgs)
    percent = round((submitted_count / total) * 100, 1) if total > 0 else 0
    
    return {
        "total": total,
        "submitted": submitted_count,
        "overdue": overdue_count,
        "not_planned": not_planned_count,
        "percent": percent,
        "items": result
    }

@router.post("/remind")
async def send_reminders(year: int = Query(default=None), quarter: int = Query(default=1), db: AsyncSession = Depends(get_db)):
    if year is None: year = date.today().year
    status_data = await get_monitoring_status(year=year, quarter=quarter, db=db)
    overdue_orgs = [item for item in status_data["items"] if item["status"] == "overdue"]
    logger.info(f"Sending reminders to {len(overdue_orgs)} organizations")
    return {"status": "success", "message": f"Напоминания отправлены ({len(overdue_orgs)} организаций)", "count": len(overdue_orgs)}

@router.post("/remind/{org_id}")
async def send_reminder_to_org(org_id: int, year: int = Query(default=None), quarter: int = Query(default=1), db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, org_id)
    if not org: raise HTTPException(status_code=404, detail="Организация не найдена")
    if not org.contact_email: raise HTTPException(status_code=400, detail="У организации не указан email")
    logger.info(f"Sending reminder to organization {org.name} ({org.contact_email})")
    return {"status": "success", "message": f"Напоминание отправлено на {org.contact_email}", "organization": org.name}

@router.get("/summary")
async def get_monitoring_summary(year: int = Query(default=None), db: AsyncSession = Depends(get_db)):
    if year is None: year = date.today().year
    results = []
    for quarter in range(1, 5):
        status = await get_monitoring_status(year=year, quarter=quarter, db=db)
        results.append({
            "quarter": quarter, "total": status["total"], "submitted": status["submitted"],
            "overdue": status["overdue"], "not_planned": status["not_planned"], "percent": status["percent"]
        })
    return {"year": year, "quarters": results}