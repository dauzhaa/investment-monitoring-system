from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.organization import Organization
from app.models.directories import District, Okved
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.report_submission import ReportSubmission
from io import BytesIO
from typing import Optional, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import date

router = APIRouter()

async def get_org_investments(db: AsyncSession, org_ids: list, year: int):
    # Факт (максимальный нарастающий итог)
    fact_res = await db.execute(
        select(InvestmentFact.organization_id, func.max(InvestmentFact.amount))
        .where(InvestmentFact.organization_id.in_(org_ids), InvestmentFact.year == year)
        .group_by(InvestmentFact.organization_id)
    )
    facts = dict(fact_res.all())
    
    # План (последнее уточнение)
    plan_subq = select(InvestmentForecast.organization_id, func.max(InvestmentForecast.id).label("mid")).where(
        InvestmentForecast.organization_id.in_(org_ids), InvestmentForecast.year == year
    ).group_by(InvestmentForecast.organization_id).subquery()
    
    plan_res = await db.execute(
        select(InvestmentForecast.organization_id, InvestmentForecast.forecast_amount)
        .join(plan_subq, InvestmentForecast.id == plan_subq.c.mid)
    )
    plans = dict(plan_res.all())
    
    # Статус сдачи (годовой)
    subm_res = await db.execute(
        select(ReportSubmission.organization_id, ReportSubmission.status)
        .where(ReportSubmission.organization_id.in_(org_ids), ReportSubmission.year == year, ReportSubmission.quarter == 4)
    )
    statuses = dict(subm_res.all())
    
    return facts, plans, statuses

@router.get("/")
async def get_organizations(
    year: int = Query(default=None), district: Optional[str] = Query(default=None),
    districts: Optional[str] = Query(default=None), smp: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None), db: AsyncSession = Depends(get_db)
):
    if year is None: year = date.today().year
        
    stmt = select(Organization).options(selectinload(Organization.district), selectinload(Organization.okved))
    
    if smp is not None: stmt = stmt.where(Organization.is_smp == smp)
    if district: stmt = stmt.join(District).where(District.name == district)
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list: stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(or_(Organization.name.ilike(search_term), Organization.inn.ilike(search_term)))
    
    stmt = stmt.order_by(Organization.name)
    orgs = (await db.execute(stmt)).scalars().all()
    
    org_ids = [org.id for org in orgs]
    facts, plans, statuses = await get_org_investments(db, org_ids, year)
    
    result = []
    for org in orgs:
        result.append({
            "id": org.id,
            "name": org.name,
            "inn": org.inn,
            "district": {"name": org.district.name} if org.district else None,
            "okved": {"code": org.okved.code} if org.okved else None,
            "is_smp": org.is_smp,
            "contact_email": org.contact_email,
            "fact_amount": float(facts.get(org.id, 0)),
            "plan_amount": float(plans.get(org.id, 0)),
            "status": statuses.get(org.id)
        })
    return result

@router.get("/count")
async def get_organizations_count(db: AsyncSession = Depends(get_db)):
    count = (await db.execute(select(func.count(Organization.id)))).scalar()
    return {"count": count}

@router.get("/export")
async def export_organizations(
    year: int = Query(default=None), districts: Optional[str] = Query(default=None),
    smp: Optional[str] = Query(default=None), db: AsyncSession = Depends(get_db)
):
    if year is None: year = date.today().year
    
    stmt = select(Organization).options(selectinload(Organization.district), selectinload(Organization.okved))
    
    if smp and smp.lower() in ['true', '1']: stmt = stmt.where(Organization.is_smp == True)
    elif smp and smp.lower() in ['false', '0']: stmt = stmt.where(Organization.is_smp == False)
    
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list: stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    orgs = (await db.execute(stmt.order_by(Organization.name))).scalars().all()
    org_ids = [org.id for org in orgs]
    facts, plans, _ = await get_org_investments(db, org_ids, year)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Организации {year}"
    
    district_names = districts if districts else "Все районы"
    ws.merge_cells('A1:H1')
    ws['A1'] = f"Отчёт об инвестициях организаций за {year} год"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    ws.merge_cells('A2:H2')
    ws['A2'] = f"Районы: {district_names}"
    ws['A2'].alignment = Alignment(horizontal='center')
    
    headers = ['№', 'Наименование', 'ИНН', 'Район', 'ОКВЭД', 'СМП', 'ФАКТ (тыс. ₽)', 'ПЛАН (тыс. ₽)']
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    for row_num, org in enumerate(orgs, 5):
        ws.cell(row=row_num, column=1, value=row_num - 4)
        ws.cell(row=row_num, column=2, value=org.name)
        ws.cell(row=row_num, column=3, value=org.inn)
        ws.cell(row=row_num, column=4, value=org.district.name if org.district else '')
        ws.cell(row=row_num, column=5, value=org.okved.code if org.okved else '')
        ws.cell(row=row_num, column=6, value='Да' if org.is_smp else 'Нет')
        ws.cell(row=row_num, column=7, value=float(facts.get(org.id, 0)))
        ws.cell(row=row_num, column=8, value=float(plans.get(org.id, 0)))
    
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 8
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 15
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"organizations_{year}_filtered.xlsx" if districts else f"organizations_{year}.xlsx"
    return StreamingResponse(
        buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{org_id}")
async def get_organization_details(org_id: int, db: AsyncSession = Depends(get_db)):
    org = await db.get(Organization, org_id)
    if not org: raise HTTPException(status_code=404, detail="Организация не найдена")

    stmt = select(Organization).options(selectinload(Organization.district), selectinload(Organization.okved)).where(Organization.id == org_id)
    org = (await db.execute(stmt)).scalar_one_or_none()

    # Собираем отчеты по годам
    years_res = await db.execute(select(func.distinct(InvestmentFact.year)).where(InvestmentFact.organization_id == org_id))
    years = sorted([y[0] for y in years_res.all()], reverse=True)
    
    reports = []
    for y in years:
        fact_res = await db.execute(select(InvestmentFact.quarter, InvestmentFact.amount).where(InvestmentFact.organization_id == org_id, InvestmentFact.year == y))
        facts_data = {row[0]: float(row[1]) for row in fact_res.all()}
        
        plan_res = await db.execute(select(InvestmentForecast.forecast_amount).where(InvestmentForecast.organization_id == org_id, InvestmentForecast.year == y).order_by(InvestmentForecast.id.desc()).limit(1))
        plan_val = plan_res.scalar_one_or_none() or 0
        
        subm_res = await db.execute(select(ReportSubmission.status).where(ReportSubmission.organization_id == org_id, ReportSubmission.year == y).limit(1))
        status = subm_res.scalar_one_or_none()
        
        reports.append({
            "year": y,
            "fact_annual": facts_data.get(None, max(facts_data.values()) if facts_data else 0),
            "forecast_annual": float(plan_val),
            "fact_q1": facts_data.get(1, 0),
            "fact_q2": facts_data.get(2, 0),
            "fact_q3": facts_data.get(3, 0),
            "fact_q4": facts_data.get(4, 0),
            "status": status
        })

    return {
        "info": {
            "id": org.id, "name": org.name, "inn": org.inn,
            "district": org.district.name if org.district else None,
            "okved": org.okved.code if org.okved else None,
            "is_smp": org.is_smp, "email": org.contact_email
        },
        "reports": reports
    }