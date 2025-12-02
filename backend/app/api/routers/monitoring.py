# backend/app/api/routers/monitoring.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.core.database import get_db
from app.models import Organization, InvestmentReport
from app.models.investment_report import ReportStatus

router = APIRouter()

@router.get("/status")
async def get_monitoring_status(
    year: int = Query(default=None, description="Год отчетности"),
    quarter: int = Query(default=None, description="Квартал (1-4)"),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
    
    orgs_res = await db.execute(select(Organization).order_by(Organization.name))
    all_orgs = orgs_res.scalars().all()
    
    reports_res = await db.execute(
        select(InvestmentReport).where(InvestmentReport.year == year)
    )
    reports_by_org = {r.organization_id: r for r in reports_res.scalars().all()}
    
    result = []
    submitted_count = 0
    
    for org in all_orgs:
        report = reports_by_org.get(org.id)
        
        if report:
            status = report.status
            if quarter:
                quarter_fact = getattr(report, f'fact_q{quarter}', 0) or 0
                status = ReportStatus.SUBMITTED.value if quarter_fact > 0 else ReportStatus.OVERDUE.value
            upload_date = report.created_at.strftime('%Y-%m-%d') if report.created_at else None
        else:
            status = ReportStatus.OVERDUE.value
            upload_date = None
        
        if status == ReportStatus.SUBMITTED.value:
            submitted_count += 1
            
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "municipality": org.municipality,
            "email": org.contact_email,
            "status": status,
            "upload_date": upload_date
        })
    
    total = len(all_orgs)
    percent = round((submitted_count / total) * 100, 1) if total > 0 else 0
        
    return {"total": total, "submitted": submitted_count, "percent": percent, "items": result}

@router.get("/export")
async def export_monitoring_report(
    year: int = Query(default=None),
    quarter: int = Query(default=0),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
    
    orgs_res = await db.execute(select(Organization).order_by(Organization.name))
    all_orgs = orgs_res.scalars().all()
    
    reports_res = await db.execute(
        select(InvestmentReport).where(InvestmentReport.year == year)
    )
    reports_by_org = {r.organization_id: r for r in reports_res.scalars().all()}
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Мониторинг {year}"
    
    headers = ["№", "Организация", "ИНН", "Район", "Прогноз", "Факт", "Статус"]
    ws.append(headers)
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1976D2")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border

    for idx, org in enumerate(all_orgs, 1):
        report = reports_by_org.get(org.id)
        if report:
            forecast = report.forecast_annual or 0
            fact = getattr(report, f'fact_q{quarter}', 0) if quarter > 0 else report.fact_annual or 0
            status = report.status
        else:
            forecast, fact = 0, 0
            status = ReportStatus.OVERDUE.value
        
        ws.append([idx, org.name, org.inn, org.municipality or "-", forecast, fact, status])
        
        for col in range(1, 8):
            cell = ws.cell(row=ws.max_row, column=col)
            cell.border = thin_border
        
        status_cell = ws.cell(row=ws.max_row, column=7)
        if status == ReportStatus.OVERDUE.value:
            status_cell.font = Font(color="FF0000", bold=True)
        else:
            status_cell.font = Font(color="2E7D32", bold=True)

    for i, w in enumerate([5, 50, 15, 20, 15, 15, 15], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        headers={'Content-Disposition': f'attachment; filename="monitoring_{year}.xlsx"'},
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@router.post("/remind")
async def send_reminders(
    year: int = Query(default=None),
    quarter: int = Query(default=None),
    organization_id: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    if year is None:
        year = datetime.now().year
    
    if organization_id:
        org = await db.get(Organization, organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Организация не найдена")
        return {"status": "success", "message": f"Напоминание отправлено для {org.name}"}
    
    return {"status": "success", "message": "Задачи на отправку писем созданы"}