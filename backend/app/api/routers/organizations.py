from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District
from io import BytesIO
from typing import Optional, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from datetime import date

router = APIRouter()


@router.get("/")
async def get_organizations(
    year: int = Query(default=None),
    district: Optional[str] = Query(default=None),
    districts: Optional[str] = Query(default=None),  # comma-separated
    smp: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Список всех организаций с фильтрацией.
    """
    if year is None:
        year = date.today().year
        
    # Базовый запрос
    stmt = select(Organization).options(
        selectinload(Organization.district),
        selectinload(Organization.okved)
    )
    
    # Фильтр по СМП
    if smp is not None:
        stmt = stmt.where(Organization.is_smp == smp)
    
    # Фильтр по одному району
    if district:
        stmt = stmt.join(District).where(District.name == district)
    
    # Фильтр по нескольким районам
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    # Поиск
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Organization.name.ilike(search_term),
                Organization.inn.ilike(search_term)
            )
        )
    
    stmt = stmt.order_by(Organization.name)
    res = await db.execute(stmt)
    orgs = res.scalars().all()
    
    # Получаем данные об инвестициях
    org_ids = [org.id for org in orgs]
    
    investments_stmt = select(
        InvestmentReport.organization_id,
        InvestmentReport.fact_annual,
        InvestmentReport.forecast_annual,
        InvestmentReport.status
    ).where(
        and_(
            InvestmentReport.organization_id.in_(org_ids),
            InvestmentReport.year == year
        )
    )
    
    inv_res = await db.execute(investments_stmt)
    investments = {row[0]: {"fact": row[1], "plan": row[2], "status": row[3]} for row in inv_res.all()}
    
    result = []
    for org in orgs:
        inv_data = investments.get(org.id, {"fact": 0, "plan": 0, "status": None})
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "district": {"name": org.district.name} if org.district else None,
            "okved": {"code": org.okved.code} if org.okved else None,
            "is_smp": org.is_smp,
            "contact_email": org.contact_email,
            "fact_amount": float(inv_data["fact"] or 0),
            "plan_amount": float(inv_data["plan"] or 0),
            "status": inv_data["status"]
        })
    
    return result


@router.get("/count")
async def get_organizations_count(db: AsyncSession = Depends(get_db)):
    """
    Общее количество организаций.
    """
    stmt = select(func.count(Organization.id))
    res = await db.execute(stmt)
    count = res.scalar()
    return {"count": count}


@router.get("/export")
async def export_organizations(
    year: int = Query(default=None),
    districts: Optional[str] = Query(default=None),
    smp: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт организаций в Excel с фильтрацией по районам.
    """
    if year is None:
        year = date.today().year
    
    # Базовый запрос
    stmt = select(Organization).options(
        selectinload(Organization.district),
        selectinload(Organization.okved)
    )
    
    # Фильтр по СМП
    if smp and smp.lower() in ['true', '1']:
        stmt = stmt.where(Organization.is_smp == True)
    elif smp and smp.lower() in ['false', '0']:
        stmt = stmt.where(Organization.is_smp == False)
    
    # Фильтр по районам
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    stmt = stmt.order_by(Organization.name)
    res = await db.execute(stmt)
    orgs = res.scalars().all()
    
    # Получаем данные об инвестициях
    org_ids = [org.id for org in orgs]
    investments_stmt = select(
        InvestmentReport.organization_id,
        InvestmentReport.fact_annual,
        InvestmentReport.forecast_annual
    ).where(
        and_(
            InvestmentReport.organization_id.in_(org_ids),
            InvestmentReport.year == year
        )
    )
    
    inv_res = await db.execute(investments_stmt)
    investments = {row[0]: {"fact": row[1], "plan": row[2]} for row in inv_res.all()}
    
    # Создаём Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Организации {year}"
    
    # Заголовок
    district_names = districts if districts else "Все районы"
    ws.merge_cells('A1:G1')
    ws['A1'] = f"Отчёт об инвестициях организаций за {year} год"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    ws.merge_cells('A2:G2')
    ws['A2'] = f"Районы: {district_names}"
    ws['A2'].alignment = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = ['№', 'Наименование', 'ИНН', 'Район', 'ОКВЭД', 'СМП', 'ФАКТ (тыс. ₽)', 'ПЛАН (тыс. ₽)']
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Данные
    for row_num, org in enumerate(orgs, 5):
        inv_data = investments.get(org.id, {"fact": 0, "plan": 0})
        ws.cell(row=row_num, column=1, value=row_num - 4)
        ws.cell(row=row_num, column=2, value=org.name)
        ws.cell(row=row_num, column=3, value=org.inn)
        ws.cell(row=row_num, column=4, value=org.district.name if org.district else '')
        ws.cell(row=row_num, column=5, value=org.okved.code if org.okved else '')
        ws.cell(row=row_num, column=6, value='Да' if org.is_smp else 'Нет')
        ws.cell(row=row_num, column=7, value=float(inv_data["fact"] or 0))
        ws.cell(row=row_num, column=8, value=float(inv_data["plan"] or 0))
    
    # Ширина столбцов
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 8
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    
    # Сохраняем в буфер
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"organizations_{year}.xlsx"
    if districts:
        filename = f"organizations_{year}_filtered.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{org_id}")
async def get_organization_details(org_id: int, db: AsyncSession = Depends(get_db)):
    """
    Полная карточка организации.
    """
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")

    # Загружаем связанные данные
    stmt = select(Organization).options(
        selectinload(Organization.district),
        selectinload(Organization.okved)
    ).where(Organization.id == org_id)
    
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()

    # Исторические отчеты
    reports_res = await db.execute(
        select(InvestmentReport)
        .where(InvestmentReport.organization_id == org_id)
        .order_by(InvestmentReport.year.desc())
    )
    reports = reports_res.scalars().all()

    return {
        "info": {
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "district": org.district.name if org.district else None,
            "okved": org.okved.code if org.okved else None,
            "is_smp": org.is_smp,
            "email": org.contact_email
        },
        "reports": [
            {
                "year": r.year,
                "fact_annual": float(r.fact_annual or 0),
                "forecast_annual": float(r.forecast_annual or 0),
                "fact_q1": float(r.fact_q1 or 0),
                "fact_q2": float(r.fact_q2 or 0),
                "fact_q3": float(r.fact_q3 or 0),
                "fact_q4": float(r.fact_q4 or 0),
                "status": r.status
            } for r in reports
        ]
    }