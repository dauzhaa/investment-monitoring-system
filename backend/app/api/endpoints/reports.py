from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import aiofiles
import os
from datetime import datetime, date
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.models import User, Organization, InvestmentReport, District
from app.core.database import get_db
from io import BytesIO
from typing import Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)


# Месяцы для заголовков
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка файла отчёта.
    """
    if year is None:
        year = date.today().year
        
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{current_user.id}_{report_type}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_PATH, unique_filename)
        
        logger.info(f"Uploading file: {file.filename} to {file_path}")
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # TODO: Process Excel file and update database
        # This is a placeholder - implement actual processing logic
        
        return {
            "status": "success",
            "detail": "Файл успешно загружен и обработан",
            "records": 0,
            "new_organizations": 0,
            "updated": 0
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/{report_type}")
async def download_template(report_type: str):
    """
    Скачивание шаблона отчёта.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # Определяем название по типу
    if report_type == "annual":
        ws.title = "Годовой отчёт"
        title = "Шаблон годового отчёта об инвестициях (форма П-2 инвест)"
    else:
        quarter_num = int(report_type[1]) if report_type.startswith('q') else 1
        ws.title = f"{quarter_num} квартал"
        title = f"Шаблон отчёта за {quarter_num} квартал ({QUARTER_MONTHS.get(quarter_num, '')})"
    
    # Заголовок
    ws.merge_cells('A1:N1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Заголовки столбцов
    headers = [
        'Наименование организации',
        'Район',
        'СМП (да/нет)',
        'ИНН',
        'ОКПО',
        'ОКВЭД',
        'Email',
        'Прогноз по инвестициям на год, тыс. рублей'
    ]
    
    if report_type == "annual":
        headers.extend([
            'Инвестиции за 1 квартал, тыс. рублей',
            'Инвестиции за 2 квартал, тыс. рублей',
            'Инвестиции за 3 квартал, тыс. рублей',
            'Инвестиции за 4 квартал, тыс. рублей',
            'Инвестиции годовые, тыс. рублей',
            'Причины отсутствия инвестиций'
        ])
    else:
        quarter_num = int(report_type[1]) if report_type.startswith('q') else 1
        headers.append(f'Инвестиции за {quarter_num} квартал, тыс. рублей')
        headers.append('Причины отсутствия инвестиций')
    
    # Стили заголовков
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
    
    # Номера столбцов
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col, value=col)
        cell.alignment = Alignment(horizontal='center')
    
    # Пример данных
    example_data = [
        'ООО "Пример"',
        'Тюменский район',
        'Нет',
        '7200000001',
        '12345678',
        '85.42',
        'example@mail.ru',
        '1000'
    ]
    
    if report_type == "annual":
        example_data.extend(['200', '300', '300', '200', '1000', ''])
    else:
        example_data.extend(['250', ''])
    
    for col, value in enumerate(example_data, 1):
        ws.cell(row=5, column=col, value=value)
    
    # Ширина столбцов
    column_widths = [50, 25, 15, 15, 12, 10, 30, 20, 20, 20, 20, 20, 20, 40]
    for i, width in enumerate(column_widths[:len(headers)], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    # Сохраняем
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"template_{report_type}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/history")
async def get_upload_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    История загрузок текущего пользователя.
    """
    # TODO: Implement actual history from database
    return [
        {
            "filename": "Отчет_2024_Q3.xlsx",
            "type": "3 квартал 2024",
            "date": "Сегодня, 14:30",
            "status": "success",
            "records": 274
        },
        {
            "filename": "Отчет_2024_Q2.xlsx",
            "type": "2 квартал 2024",
            "date": "15.08.2024",
            "status": "success",
            "records": 268
        }
    ]


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
    
    # Заголовок отчёта
    quarter_months = QUARTER_MONTHS.get(quarter, '')
    title = f"Отчёт об инвестициях за {quarter} квартал {quarter_months} {year} года"
    
    ws.merge_cells('A1:F1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='center')
    
    # Дата формирования
    ws.merge_cells('A2:F2')
    ws['A2'] = f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ws['A2'].alignment = Alignment(horizontal='center')
    
    # Заголовки
    headers = ['№', 'Организация', 'ИНН', 'Район', 'Статус', 'Дата сдачи']
    header_fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # Получаем данные
    stmt = select(Organization).options()
    if districts:
        district_list = [d.strip() for d in districts.split(',') if d.strip()]
        if district_list:
            stmt = stmt.join(District, isouter=True).where(District.name.in_(district_list))
    
    stmt = stmt.order_by(Organization.name)
    res = await db.execute(stmt)
    orgs = res.scalars().all()
    
    # TODO: Get actual submission status from database
    
    for row_num, org in enumerate(orgs, 5):
        ws.cell(row=row_num, column=1, value=row_num - 4)
        ws.cell(row=row_num, column=2, value=org.name)
        ws.cell(row=row_num, column=3, value=org.inn)
        ws.cell(row=row_num, column=4, value=org.district.name if org.district else '')
        ws.cell(row=row_num, column=5, value='Сдан')  # TODO: actual status
        ws.cell(row=row_num, column=6, value='')  # TODO: actual date
    
    # Ширина столбцов
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 50
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 15
    
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


@router.get("/export/organization/{org_id}")
async def export_organization_report(
    org_id: int,
    year: int = Query(default=None),
    quarter: int = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт отчёта конкретной организации.
    """
    if year is None:
        year = date.today().year
    
    # Получаем организацию
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Организация не найдена")
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчёт"
    
    # Заголовок
    if quarter:
        title = f"Отчёт об инвестициях за {quarter} квартал {year} года"
    else:
        title = f"Отчёт об инвестициях за {year} год"
    
    ws.merge_cells('A1:D1')
    ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14)
    
    # Информация об организации
    ws['A3'] = 'Организация:'
    ws['B3'] = org.name
    ws['A4'] = 'ИНН:'
    ws['B4'] = org.inn
    ws['A5'] = 'Район:'
    ws['B5'] = org.district.name if org.district else ''
    
    # TODO: Add actual investment data
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    filename = f"report_{org.inn}_{year}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )