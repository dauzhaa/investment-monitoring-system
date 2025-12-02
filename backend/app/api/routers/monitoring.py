from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload  # <--- ДОБАВЛЕНО
from app.core.database import get_db
# ИСПРАВЛЕНО: OKVED -> Okved
from app.models import Organization, InvestmentReport, District, Okved 
from pydantic import BaseModel
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

router = APIRouter()

class RemindRequest(BaseModel):
    organization_id: int
    year: int
    quarter: int
    email: str

@router.get("/status")
async def get_monitoring_status(
    year: int, 
    quarter: int,  # 0 = весь год
    db: AsyncSession = Depends(get_db)
):
    """
    Статус сдачи отчетности.
    """
    orgs_res = await db.execute(
        select(Organization)
        .options(
            selectinload(Organization.district),
            # Если нужно подгружать ОКВЭД, раскомментируй:
            # selectinload(Organization.okved) 
        )
        .order_by(Organization.name)
    )
    all_orgs = orgs_res.scalars().all()
    
    reports_stmt = select(InvestmentReport).where(InvestmentReport.year == year)
    reports_res = await db.execute(reports_stmt)
    reports_by_org = {r.organization_id: r for r in reports_res.scalars().all()}
    
    result = []
    submitted_count = 0
    
    for org in all_orgs:
        report = reports_by_org.get(org.id)
        is_submitted = False
        
        if report:
            if quarter == 0:
                is_submitted = report.fact_annual > 0
            elif quarter == 1:
                is_submitted = report.fact_q1 > 0
            elif quarter == 2:
                is_submitted = report.fact_q2 > 0
            elif quarter == 3:
                is_submitted = report.fact_q3 > 0
            elif quarter == 4:
                is_submitted = report.fact_q4 > 0
        
        if is_submitted:
            submitted_count += 1
            
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "district": org.district.name if org.district else "Не указан",
            "email": org.contact_email,
            "status": "submitted" if is_submitted else "overdue"
        })
        
    return {
        "total": len(all_orgs),
        "submitted": submitted_count,
        "items": result
    }

@router.post("/remind")
async def send_reminder(remind_data: RemindRequest):
    print(f"📧 SENDING EMAIL TO: {remind_data.email}")
    return {"status": "success", "message": "Напоминание отправлено"}

@router.get("/export/quarterly")
async def export_quarterly_report(
    year: int,
    quarter: int,
    db: AsyncSession = Depends(get_db)
):
    orgs_res = await db.execute(
        select(Organization)
        .options(selectinload(Organization.district), selectinload(Organization.okved))
        .order_by(Organization.name)
    )
    all_orgs = orgs_res.scalars().all()
    
    reports_res = await db.execute(select(InvestmentReport).where(InvestmentReport.year == year))
    reports = {r.organization_id: r for r in reports_res.scalars().all()}
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    q_name = "Весь год" if quarter == 0 else f"{quarter} Квартал (Накопительно)"
    ws.title = f"Отчет {year}"
    
    headers = ["Наименование", "ИНН", "Район", "ОКВЭД", "ОКПО", "Почта", f"Сумма ({q_name})", "Статус"]
    ws.append(headers)
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
    
    for org in all_orgs:
        report = reports.get(org.id)
        amount = 0.0
        status = "Не сдан"
        
        if report:
            q1 = report.fact_q1 or 0
            q2 = report.fact_q2 or 0
            q3 = report.fact_q3 or 0
            q4 = report.fact_q4 or 0
            
            if quarter == 0:
                amount = report.fact_annual
                status = "Сдан" if amount > 0 else "Не сдан"
            elif quarter == 1:
                amount = q1
                status = "Сдан" if q1 > 0 else "Не сдан"
            elif quarter == 2:
                amount = q1 + q2
                status = "Сдан" if q2 > 0 else "Не сдан"
            elif quarter == 3:
                amount = q1 + q2 + q3
                status = "Сдано" if q3 > 0 else "Не сдано"
            elif quarter == 4:
                amount = q1 + q2 + q3 + q4
                status = "Сдано" if q4 > 0 else "Не сдано"
        
        ws.append([
            org.name, 
            org.inn, 
            org.district.name if org.district else "-",
            org.okved.code if org.okved else "-",
            "", # ОКПО
            org.contact_email or "-",
            amount,
            status
        ])
    
    # Автоширина
    for col in ws.columns:
        max_len = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_len:
                    max_len = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = min(max_len + 2, 50)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"report_{year}_q{quarter}.xlsx"
    return StreamingResponse(
        output, 
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@router.get("/export/organization/{org_id}")
async def export_organization_report(
    org_id: int,
    year: int,
    quarter: int,
    db: AsyncSession = Depends(get_db)
):
    # Упрощенная заглушка для скачивания отчета одной организации (использует общую логику для простоты примера)
    # В реале тут детальный отчет
    return await export_quarterly_report(year, quarter, db)