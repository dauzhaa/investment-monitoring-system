from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import aiofiles
import os
from datetime import datetime, date
from app.core.config import settings
from app.core.database import get_db
from app.models import Organization, InvestmentReport, District
from io import BytesIO
from typing import Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)

QUARTER_MONTHS = {
    1: "январь-март",
    2: "апрель-июнь", 
    3: "июль-сентябрь",
    4: "октябрь-декабрь"
}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    report_type: str = Form(default="annual"),
    year: int = Form(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка файла отчёта.
    Авторизация убрана для упрощения тестирования.
    """
    if year is None:
        year = date.today().year
        
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{report_type}_{year}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_PATH, unique_filename)
        
        logger.info(f"Uploading file: {file.filename} to {file_path}")
        
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Обработка Excel файла
        records_count = 0
        new_orgs = 0
        updated = 0
        errors = []
        
        try:
            wb = openpyxl.load_workbook(BytesIO(content))
            ws = wb.active
            
            # Пропускаем заголовки (первые 2 строки)
            for row_idx, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
                if row[0] is None:
                    continue
                    
                records_count += 1
                
                try:
                    org_name = str(row[0]).strip() if row[0] else None
                    district_name = str(row[1]).strip() if row[1] else None
                    is_smp = str(row[2]).strip().lower() in ['да', 'yes', '1', 'true'] if row[2] else False
                    inn = str(int(row[3])) if row[3] else None
                    okpo = str(row[4]).strip() if row[4] else None
                    okved = str(row[5]).strip() if row[5] else None
                    email = str(row[6]).strip() if row[6] else None
                    
                    # Прогноз на год (столбец 8, индекс 7)
                    forecast = float(row[7]) if row[7] else 0
                    
                    # Инвестиции по кварталам (столбцы 9-12, индексы 8-11)
                    q1 = float(row[8]) if len(row) > 8 and row[8] else 0
                    q2 = float(row[9]) if len(row) > 9 and row[9] else 0
                    q3 = float(row[10]) if len(row) > 10 and row[10] else 0
                    q4 = float(row[11]) if len(row) > 11 and row[11] else 0
                    
                    # Годовые инвестиции (столбец 13, индекс 12)
                    annual = float(row[12]) if len(row) > 12 and row[12] else 0
                    
                    # TODO: Сохранение в БД
                    # Здесь должна быть логика создания/обновления Organization и InvestmentReport
                    
                except Exception as row_error:
                    errors.append(f"Строка {row_idx}: {str(row_error)}")
                    logger.warning(f"Error processing row {row_idx}: {row_error}")
                    
        except Exception as parse_error:
            logger.error(f"Excel parse error: {str(parse_error)}")
            raise HTTPException(status_code=400, detail=f"Ошибка парсинга Excel: {str(parse_error)}")
        
        return {
            "status": "success",
            "detail": "Файл успешно загружен и обработан",
            "records": records_count,
            "new_organizations": new_orgs,
            "updated": updated,
            "errors": errors[:10] if errors else []  # Первые 10 ошибок
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/{report_type}")
async def download_template(report_type: str):
    """
    Скачивание шаблона отчёта.
    Формат: название орг, инн, оквэд, окпо, смп, инвестиции за квартал (или год)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    
    if report_type == "annual":
        ws.title = "Годовой отчёт"
        title = "Шаблон годового отчёта об инвестициях (форма П-2 инвест)"
    else:
        quarter_num = int(report_type[1]) if report_type.startswith('q') else 1
        ws.title = f"{quarter_num} квартал"
        title = f"Шаблон отчёта за {quarter_num} квартал ({QUARTER_MONTHS.get(quarter_num, '')})"
    
    # Заголовок
    ws.merge_cells('A1:F1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = [
        'Наименование организации',
        'ИНН',
        'ОКВЭД',
        'ОКПО',
        'СМП (да/нет)',
    ]
    
    if report_type == "annual":
        headers.append('Инвестиции за год, тыс. рублей')
    else:
        quarter_num = int(report_type[1]) if report_type.startswith('q') else 1
        headers.append(f'Инвестиции за {quarter_num} квартал, тыс. рублей')
    
    # Стили заголовков
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
    
    # Пример данных
    example_data = ['ООО "Пример"', '7200000001', '85.42', '12345678', 'Нет', '1000']
    for col, value in enumerate(example_data, 1):
        ws.cell(row=4, column=col, value=value)
    
    # Ширина столбцов
    column_widths = [50, 15, 10, 12, 12, 25]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    # Сохраняем в буфер
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"template_{report_type}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/organization/{org_id}")
async def export_organization_report(
    org_id: int,
    year: int = Query(default=None),
    quarter: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт отчёта конкретной организации.
    Формат: название орг, инн, оквэд, окпо, смп, инвестиции за квартал (или год)
    """
    if year is None:
        year = date.today().year
    
    # Получаем организацию с связанными данными
    stmt = select(Organization).options(
        selectinload(Organization.district),
        selectinload(Organization.okved)
    ).where(Organization.id == org_id)
    
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    
    # Получаем данные инвестиций
    report_stmt = select(InvestmentReport).where(
        and_(
            InvestmentReport.organization_id == org_id,
            InvestmentReport.year == year
        )
    )
    report_result = await db.execute(report_stmt)
    report = report_result.scalar_one_or_none()
    
    # Создаём Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    
    if quarter:
        ws.title = f"Q{quarter} {year}"
        title = f"Отчёт об инвестициях за {quarter} квартал {QUARTER_MONTHS.get(quarter, '')} {year} года"
    else:
        ws.title = f"Год {year}"
        title = f"Отчёт об инвестициях за {year} год"
    
    # Заголовок
    ws.merge_cells('A1:F1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = ['Наименование', 'ИНН', 'ОКВЭД', 'ОКПО', 'СМП', 'Инвестиции (тыс. ₽)']
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Данные организации
    ws.cell(row=4, column=1, value=org.name)
    ws.cell(row=4, column=2, value=org.inn)
    ws.cell(row=4, column=3, value=org.okved.code if org.okved else '')
    ws.cell(row=4, column=4, value=org.okpo if hasattr(org, 'okpo') else '')
    ws.cell(row=4, column=5, value='Да' if org.is_smp else 'Нет')
    
    # Инвестиции
    investment_value = 0
    if report:
        if quarter:
            quarter_map = {1: 'fact_q1', 2: 'fact_q2', 3: 'fact_q3', 4: 'fact_q4'}
            investment_value = getattr(report, quarter_map.get(quarter, 'fact_annual'), 0) or 0
        else:
            investment_value = report.fact_annual or 0
    
    ws.cell(row=4, column=6, value=investment_value)
    
    # Ширина столбцов
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 8
    ws.column_dimensions['F'].width = 20
    
    # Сохраняем
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"report_{org.inn}_{year}.xlsx"
    if quarter:
        filename = f"report_{org.inn}_Q{quarter}_{year}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/monitoring")
async def export_monitoring_report(
    year: int = Query(default=None),
    quarter: int = Query(default=1),
    districts: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт отчёта мониторинга сдачи.
    """
    if year is None:
        year = date.today().year
    
    # Создаём Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Мониторинг Q{quarter} {year}"
    
    quarter_months = QUARTER_MONTHS.get(quarter, '')
    title = f"Отчёт об инвестициях за {quarter} квартал {quarter_months} {year} года"
    
    # Заголовок
    ws.merge_cells('A1:F1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    ws.merge_cells('A2:F2')
    ws['A2'] = f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ws['A2'].alignment = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = ['№', 'Организация', 'ИНН', 'Район', 'Статус', 'Email']
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Получаем организации
    stmt = select(Organization).options(
        selectinload(Organization.district)
    ).order_by(Organization.name)
    
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    result = await db.execute(stmt)
    orgs = result.scalars().all()
    
    # Получаем отчёты за период
    reports_stmt = select(InvestmentReport).where(
        InvestmentReport.year == year
    )
    reports_result = await db.execute(reports_stmt)
    reports = {r.organization_id: r for r in reports_result.scalars().all()}
    
    # Заполняем данные
    row_num = 5
    for idx, org in enumerate(orgs, 1):
        report = reports.get(org.id)
        
        # Определяем статус
        quarter_map = {1: 'fact_q1', 2: 'fact_q2', 3: 'fact_q3', 4: 'fact_q4'}
        quarter_field = quarter_map.get(quarter, 'fact_annual')
        
        if report:
            quarter_value = getattr(report, quarter_field, 0) or 0
            forecast = report.forecast_annual or 0
            
            if quarter_value > 0:
                status = 'Сдан'
            elif forecast > 0:
                status = 'Просрочка'
            else:
                status = 'Не запланировано'
        else:
            status = 'Нет данных'
        
        ws.cell(row=row_num, column=1, value=idx)
        ws.cell(row=row_num, column=2, value=org.name)
        ws.cell(row=row_num, column=3, value=org.inn)
        ws.cell(row=row_num, column=4, value=org.district.name if org.district else '')
        ws.cell(row=row_num, column=5, value=status)
        ws.cell(row=row_num, column=6, value=org.contact_email or '')
        
        row_num += 1
    
    # Ширина столбцов
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 30
    
    # Сохраняем
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"monitoring_Q{quarter}_{year}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/history")
async def get_upload_history(db: AsyncSession = Depends(get_db)):
    """
    История загрузок.
    """
    # TODO: Реализовать получение из БД
    return [
        {
            "filename": "Отчет_2022_annual.xlsx",
            "type": "Годовой 2022",
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "status": "success",
            "records": 287
        }
    ]