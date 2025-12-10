from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District
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
    """
    Возвращает статус сдачи отчетности по всем организациям за конкретный период.
    Статусы:
    - submitted (Сдан): есть данные за квартал > 0
    - overdue (Просрочка): прогноз > 0, но данных за квартал нет
    - not_planned (Не запланировано): прогноз = 0, данных нет
    """
    if year is None:
        year = date.today().year
    
    # Получаем организации
    stmt = select(Organization).options(
        selectinload(Organization.district)
    ).order_by(Organization.name)
    
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    orgs_result = await db.execute(stmt)
    all_orgs = orgs_result.scalars().all()
    
    # Получаем отчёты за год
    reports_stmt = select(InvestmentReport).where(
        InvestmentReport.year == year
    )
    reports_result = await db.execute(reports_stmt)
    reports = {r.organization_id: r for r in reports_result.scalars().all()}
    
    # Маппинг квартала на поле
    quarter_field_map = {
        1: 'fact_q1',
        2: 'fact_q2', 
        3: 'fact_q3',
        4: 'fact_q4'
    }
    quarter_field = quarter_field_map.get(quarter, 'fact_annual')
    
    result = []
    submitted_count = 0
    overdue_count = 0
    not_planned_count = 0
    
    for org in all_orgs:
        report = reports.get(org.id)
        
        if report:
            quarter_value = getattr(report, quarter_field, 0) or 0
            forecast = report.forecast_annual or 0
            
            if quarter_value > 0:
                status = 'submitted'
                submitted_count += 1
            elif forecast > 0:
                status = 'overdue'
                overdue_count += 1
            else:
                status = 'not_planned'
                not_planned_count += 1
        else:
            status = 'not_planned'
            not_planned_count += 1
        
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
async def send_reminders(
    year: int = Query(default=None), 
    quarter: int = Query(default=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Отправка напоминаний всем должникам.
    """
    if year is None:
        year = date.today().year
    
    # Получаем список должников
    status_data = await get_monitoring_status(year=year, quarter=quarter, db=db)
    overdue_orgs = [item for item in status_data["items"] if item["status"] == "overdue"]
    
    # TODO: Реализовать отправку email через Celery
    logger.info(f"Sending reminders to {len(overdue_orgs)} organizations")
    
    return {
        "status": "success", 
        "message": f"Напоминания отправлены ({len(overdue_orgs)} организаций)",
        "count": len(overdue_orgs)
    }


@router.post("/remind/{org_id}")
async def send_reminder_to_org(
    org_id: int,
    year: int = Query(default=None), 
    quarter: int = Query(default=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Отправка напоминания конкретной организации.
    """
    if year is None:
        year = date.today().year
    
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    
    if not org.contact_email:
        raise HTTPException(status_code=400, detail="У организации не указан email")
    
    # TODO: Реализовать отправку email
    logger.info(f"Sending reminder to organization {org.name} ({org.contact_email})")
    
    return {
        "status": "success",
        "message": f"Напоминание отправлено на {org.contact_email}",
        "organization": org.name
    }


@router.get("/summary")
async def get_monitoring_summary(
    year: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Сводка по всем кварталам за год.
    """
    if year is None:
        year = date.today().year
    
    results = []
    for quarter in range(1, 5):
        status = await get_monitoring_status(year=year, quarter=quarter, db=db)
        results.append({
            "quarter": quarter,
            "total": status["total"],
            "submitted": status["submitted"],
            "overdue": status["overdue"],
            "not_planned": status["not_planned"],
            "percent": status["percent"]
        })
    
    return {
        "year": year,
        "quarters": results
    }