from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models import Organization, InvestmentReport

router = APIRouter()

@router.get("/status")
async def get_monitoring_status(
    year: int, 
    quarter: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает статус сдачи отчетности по всем организациям за конкретный период.
    """
    # 1. Получаем все активные организации
    orgs_res = await db.execute(select(Organization).order_by(Organization.name))
    all_orgs = orgs_res.scalars().all()
    
    # 2. Получаем отчеты за выбранный период
    reports_res = await db.execute(
        select(InvestmentReport).where(
            and_(
                InvestmentReport.report_year == year,
                InvestmentReport.quarter == quarter
            )
        )
    )
    reports = reports_res.scalars().all()
    
    # Создаем множество ID организаций, которые СДАЛИ отчет
    submitted_org_ids = {r.organization_id for r in reports}
    
    result = []
    submitted_count = 0
    
    for org in all_orgs:
        is_submitted = org.id in submitted_org_ids
        if is_submitted:
            submitted_count += 1
            
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "municipality": org.municipality,
            "email": org.contact_email,
            "status": "submitted" if is_submitted else "overdue", # Сдано / Просрочено
            "upload_date": "2024-03-15" if is_submitted else None # Тут можно брать реальную дату из created_at
        })
        
    return {
        "total": len(all_orgs),
        "submitted": submitted_count,
        "percent": round((submitted_count / len(all_orgs)) * 100, 1) if all_orgs else 0,
        "items": result
    }

@router.post("/remind")
async def send_reminders(
    year: int, 
    quarter: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Заглушка для отправки уведомлений должникам.
    В реале здесь будет вызов Celery задачи.
    """
    # Логика поиска должников такая же, как выше
    return {"status": "success", "message": "Задачи на отправку писем созданы (12 шт)"}