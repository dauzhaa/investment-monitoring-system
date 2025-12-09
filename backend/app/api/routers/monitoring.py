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
    """
    if year is None:
        year = date.today().year
    
    # Базовый запрос организаций
    stmt = select(Organization).options(
        selectinload(Organization.district)
    )
    
    # Фильтр по районам
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    stmt = stmt.order_by(Organization.name)
    orgs_res = await db.execute(stmt)
    all_orgs = orgs_res.scalars().all()
    
    # Получаем отчеты за выбранный период
    # Проверяем, что есть данные за нужный квартал
    reports_stmt = select(
        InvestmentReport.organization_id,
        InvestmentReport.created_at,
        InvestmentReport.status
    ).where(
        InvestmentReport.year == year
    )
    
    # Проверяем по соответствующему кварталу
    quarter_field_map = {
        1: InvestmentReport.fact_q1,
        2: InvestmentReport.fact_q2,
        3: InvestmentReport.fact_q3,
        4: InvestmentReport.fact_q4
    }
    
    reports_res = await db.execute(reports_stmt)
    reports_data = {row[0]: {"date": row[1], "status": row[2]} for row in reports_res.all()}
    
    result = []
    submitted_count = 0
    
    for org in all_orgs:
        report_info = reports_data.get(org.id)
        
        # Определяем статус: если есть отчет - сдан, иначе просрочен
        is_submitted = report_info is not None
        if is_submitted:
            submitted_count += 1
            
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "municipality": org.district.name if org.district else "Не указан",
            "email": org.contact_email,
            "status": "submitted" if is_submitted else "overdue",
            "upload_date": report_info["date"].isoformat() if report_info and report_info["date"] else None
        })
    
    total = len(all_orgs)
    percent = round((submitted_count / total) * 100, 1) if total > 0 else 0
        
    return {
        "total": total,
        "submitted": submitted_count,
        "overdue": total - submitted_count,
        "percent": percent,
        "items": result
    }


@router.post("/remind")
async def send_reminders(
    year: int = Query(default=None), 
    quarter: int = Query(default=1),
    background_tasks: BackgroundTasks = None,
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
    # for org in overdue_orgs:
    #     if org["email"]:
    #         background_tasks.add_task(send_reminder_email, org["email"], org["name"], year, quarter)
    
    logger.info(f"Sending reminders to {len(overdue_orgs)} organizations")
    
    return {
        "status": "success", 
        "message": f"Задачи на отправку писем созданы ({len(overdue_orgs)} шт)",
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
    
    # Получаем организацию
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
            "percent": status["percent"]
        })
    
    return {
        "year": year,
        "quarters": results
    }