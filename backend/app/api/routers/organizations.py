from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import Organization, InvestmentReport
from fastapi.responses import StreamingResponse
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side

router = APIRouter()

@router.get("/")
async def get_organizations(db: AsyncSession = Depends(get_db)):
    """
    Список всех организаций для таблицы.
    Возвращает базовую инфу + сумму инвестиций + кластер.
    """
    # Считаем сумму инвестиций для каждой организации
    subquery = select(
        InvestmentReport.organization_id,
        func.sum(InvestmentReport.total_investment).label("total_money")
    ).group_by(InvestmentReport.organization_id).subquery()

    # Соединяем организации с их деньгами
    stmt = select(Organization, subquery.c.total_money).outerjoin(
        subquery, Organization.id == subquery.c.organization_id
    ).order_by(Organization.name)

    res = await db.execute(stmt)
    orgs = []
    for row in res.all():
        org, total = row
        orgs.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "municipality": org.municipality,
            "cluster_group": org.cluster_group, # 0, 1, 2
            "total_investment": total if total else 0
        })
    return orgs

@router.get("/{org_id}")
async def get_organization_details(org_id: int, db: AsyncSession = Depends(get_db)):
    """
    Полная карточка организации:
    1. Инфо
    2. История отчетов (для таблицы внутри карточки)
    3. Прогноз AI (для графика)
    """
    # 1. Сама организация
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    # 2. Исторические отчеты
    reports_res = await db.execute(
        select(InvestmentReport)
        .where(InvestmentReport.organization_id == org_id)
        .order_by(InvestmentReport.report_year, InvestmentReport.quarter)
    )
    reports = reports_res.scalars().all()

    forecast_data = []
    for report in reports:
        if report.forecast_annual > 0:
            forecast_data.append({
                "year": report.year,
                "amount": report.forecast_annual
            })

    return {
        "info": {
            "name": org.name,
            "inn": org.inn,
            "municipality": org.municipality,
            "email": org.contact_email
        },
        "reports": [
            {
                "year": r.report_year, 
                "quarter": r.quarter, 
                "amount": r.total_investment,
                "source_fed": r.budget_federal,
                "source_reg": r.budget_regional
            } for r in reports
        ],
    }
    
@router.get("/export/summary")
async def export_summary_report(
    year: int, 
    quarter: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Генерация Excel файла со статусами сдачи отчетности.
    """
    # 1. Получаем данные (используем ту же логику, что и в status)
    # (В идеале вынести логику получения данных в отдельную сервисную функцию, 
    #  но сейчас скопируем для скорости)
    
    orgs_res = await db.execute(select(Organization).order_by(Organization.name))
    all_orgs = orgs_res.scalars().all()
    
    reports_res = await db.execute(
        select(InvestmentReport).where(
            and_(
                InvestmentReport.report_year == year,
                InvestmentReport.quarter == quarter
            )
        )
    )
    reports = {r.organization_id: r for r in reports_res.scalars().all()}
    
    # 2. Создаем Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Отчет {year} Q{quarter}"
    
    # Заголовки
    headers = ["Наименование", "ИНН", "Район", "Сумма инвестиций", "Статус"]
    ws.append(headers)
    
    # Стили
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    # Данные
    for org in all_orgs:
        report = reports.get(org.id)
        status = "Сдано" if report else "Не сдано"
        amount = report.total_investment if report else 0
        
        row = [org.name, org.inn, org.municipality, amount, status]
        ws.append(row)
        
        # Красим ячейку статуса
        current_row = ws.max_row
        status_cell = ws.cell(row=current_row, column=5)
        if status == "Не сдано":
            status_cell.font = Font(color="FF0000")
        else:
            status_cell.font = Font(color="008000")

    # Автоширина колонок
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    # 3. Отдаем файл
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"monitor_{year}_q{quarter}.xlsx"
    
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )