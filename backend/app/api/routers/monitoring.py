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
    # Заголовки накопительных периодов
    period_names = {
        0: "январь-декабрь (год)",
        1: "январь-март",
        2: "январь-июнь",
        3: "январь-сентябрь",
        4: "январь-декабрь"
    }
    period_str = period_names.get(quarter, "")

    # Загружаем данные
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
    ws.title = f"Отчет {year}"
    
    # Формируем шапку как в initial data
    headers = [
        "Наименование организации",
        "ИНН",
        "Район",
        "ОКВЭД",
        "ОКПО", # Оставляем пустым или берем если есть
        "Почта",
        f"Инвестиции за {quarter} квартал {period_str} {year} г., тыс. рублей",
        "Статус"
    ]
    ws.append(headers)
    
    # Стили шапки
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    
    ws.row_dimensions[1].height = 40

    for org in all_orgs:
        report = reports.get(org.id)
        amount = 0.0
        status = "Не сдан"
        
        if report:
            # Берем конкретное поле из базы, так как они там уже лежат накопительно (из парсера)
            if quarter == 0: 
                amount = report.fact_annual
                status = "Сдан" if report.fact_annual > 0 else report.status
            elif quarter == 1: 
                amount = report.fact_q1
                status = "Сдан" if report.fact_q1 > 0 else report.status
            elif quarter == 2: 
                amount = report.fact_q2
                status = "Сдан" if report.fact_q2 > 0 else report.status
            elif quarter == 3: 
                amount = report.fact_q3
                status = "Сдан" if report.fact_q3 > 0 else report.status
            elif quarter == 4: 
                amount = report.fact_q4
                status = "Сдан" if report.fact_q4 > 0 else report.status
        
        row_data = [
            org.name, 
            org.inn, 
            org.district.name if org.district else "-",
            org.okved.code if org.okved else "-",
            "", # ОКПО нет в базе пока
            org.contact_email or "-",
            amount,
            status
        ]
        ws.append(row_data)
        
        # Границы для ячеек
        for cell in ws[ws.max_row]:
            cell.border = thin_border

    # Автоширина
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 25
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 25
    ws.column_dimensions['G'].width = 20
    ws.column_dimensions['H'].width = 15

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