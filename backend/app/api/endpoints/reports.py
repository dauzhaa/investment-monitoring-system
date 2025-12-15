from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
from datetime import datetime, date
from io import BytesIO
from typing import Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_PATH = os.environ.get('UPLOAD_PATH', './uploads')
os.makedirs(UPLOAD_PATH, exist_ok=True)

QUARTER_MONTHS = {1: "январь-март", 2: "апрель-июнь", 3: "июль-сентябрь", 4: "октябрь-декабрь"}

# Стили Excel
HEADER_FILL = PatternFill(start_color='5C6BC0', end_color='5C6BC0', fill_type='solid')
HEADER_FONT = Font(bold=True, color='FFFFFF', size=11)
MONEY_FORMAT = '#,##0.00" тыс. ₽"'
THIN_BORDER = Border(
    left=Side(style='thin', color='CCCCCC'),
    right=Side(style='thin', color='CCCCCC'),
    top=Side(style='thin', color='CCCCCC'),
    bottom=Side(style='thin', color='CCCCCC')
)

def style_header(ws, row, cols):
    for col in range(1, cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = THIN_BORDER

def apply_money(cell):
    cell.number_format = MONEY_FORMAT
    cell.border = THIN_BORDER

# Mock данные
YEARLY_DATA = [
    {"year": 2022, "fact": 390509, "plan": 393401},
    {"year": 2023, "fact": 420000, "plan": 410000},
    {"year": 2024, "fact": 450000, "plan": 440000},
    {"year": 2025, "fact": 384379, "plan": 470000},
]

DISTRICTS_DATA = [
    {"name": "г. Тюмень", "fact": 169154, "plan": 170000, "orgs": 89},
    {"name": "Тюменский район", "fact": 51465, "plan": 52000, "orgs": 28},
    {"name": "г. Ишим", "fact": 22902, "plan": 23000, "orgs": 12},
    {"name": "г. Тобольск", "fact": 19551, "plan": 20000, "orgs": 18},
    {"name": "Тобольский район", "fact": 15641, "plan": 16000, "orgs": 14},
    {"name": "Ишимский район", "fact": 14500, "plan": 15000, "orgs": 15},
    {"name": "г. Ялуторовск", "fact": 11731, "plan": 12000, "orgs": 8},
    {"name": "Ялуторовский район", "fact": 9773, "plan": 10000, "orgs": 7},
    {"name": "г. Заводоуковск", "fact": 8500, "plan": 9000, "orgs": 6},
    {"name": "Заводоуковский район", "fact": 7818, "plan": 8000, "orgs": 6},
    {"name": "Голышмановский район", "fact": 6500, "plan": 7000, "orgs": 5},
    {"name": "Исетский район", "fact": 5864, "plan": 6000, "orgs": 5},
    {"name": "Уватский район", "fact": 5500, "plan": 5800, "orgs": 5},
    {"name": "Нижнетавдинский район", "fact": 4886, "plan": 5000, "orgs": 4},
    {"name": "Упоровский район", "fact": 4500, "plan": 4700, "orgs": 4},
    {"name": "Армизонский район", "fact": 3909, "plan": 4000, "orgs": 4},
    {"name": "Аромашевский район", "fact": 3500, "plan": 3700, "orgs": 4},
    {"name": "Бердюжский район", "fact": 3421, "plan": 3500, "orgs": 4},
    {"name": "Вагайский район", "fact": 3200, "plan": 3400, "orgs": 4},
    {"name": "Викуловский район", "fact": 2932, "plan": 3000, "orgs": 3},
    {"name": "Абатский район", "fact": 2800, "plan": 3000, "orgs": 3},
    {"name": "Казанский район", "fact": 2443, "plan": 2600, "orgs": 3},
    {"name": "Омутинский район", "fact": 2200, "plan": 2400, "orgs": 3},
    {"name": "Сладковский район", "fact": 1954, "plan": 2100, "orgs": 2},
    {"name": "Сорокинский район", "fact": 1800, "plan": 2000, "orgs": 2},
    {"name": "Юргинский район", "fact": 1466, "plan": 1600, "orgs": 3},
    {"name": "Ярковский район", "fact": 977, "plan": 1100, "orgs": 2},
]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), report_type: str = Form(default="annual"), year: int = Form(default=None)):
    if year is None:
        year = date.today().year
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{report_type}_{year}_{file.filename}"
        path = os.path.join(UPLOAD_PATH, filename)
        content = await file.read()
        async with aiofiles.open(path, 'wb') as f:
            await f.write(content)
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        count = sum(1 for row in ws.iter_rows(min_row=3, values_only=True) if row[0])
        return {"status": "success", "records": count, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/{report_type}")
async def download_template(report_type: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Шаблон"
    headers = ['Наименование', 'ИНН', 'ОКВЭД', 'ОКПО', 'СМП', 'Инвестиции, тыс. ₽']
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    style_header(ws, 1, len(headers))
    ws.cell(row=2, column=1, value='ООО "Пример"')
    ws.cell(row=2, column=6, value=1000)
    apply_money(ws.cell(row=2, column=6))
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename=template_{report_type}.xlsx"})


@router.get("/export/yearly")
async def export_yearly():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "По годам"
    ws.merge_cells('A1:D1')
    ws['A1'] = "Динамика инвестиций 2022-2025"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = f"Сформировано: {datetime.now().strftime('%d.%m.%Y')}"
    headers = ['Год', 'ФАКТ, тыс. ₽', 'ПЛАН, тыс. ₽', 'Освоение, %']
    for col, h in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=h)
    style_header(ws, 4, 4)
    for i, d in enumerate(YEARLY_DATA, 5):
        ws.cell(row=i, column=1, value=d["year"])
        c2 = ws.cell(row=i, column=2, value=d["fact"])
        apply_money(c2)
        c3 = ws.cell(row=i, column=3, value=d["plan"])
        apply_money(c3)
        pct = round(d["fact"] / d["plan"] * 100, 1) if d["plan"] else 0
        ws.cell(row=i, column=4, value=f"{pct}%")
    for col in [1, 2, 3, 4]:
        ws.column_dimensions[get_column_letter(col)].width = 20
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=yearly_2022-2025.xlsx"})


@router.get("/export/districts")
async def export_districts(year: int = Query(default=2022)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Районы {year}"
    ws.merge_cells('A1:E1')
    ws['A1'] = f"Инвестиции по районам Тюменской области за {year} год"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = f"Сформировано: {datetime.now().strftime('%d.%m.%Y')}"
    headers = ['Район', 'Организаций', 'ФАКТ, тыс. ₽', 'ПЛАН, тыс. ₽', 'Освоение, %']
    for col, h in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=h)
    style_header(ws, 4, 5)
    for i, d in enumerate(DISTRICTS_DATA, 5):
        ws.cell(row=i, column=1, value=d["name"])
        ws.cell(row=i, column=2, value=d["orgs"])
        c3 = ws.cell(row=i, column=3, value=d["fact"])
        apply_money(c3)
        c4 = ws.cell(row=i, column=4, value=d["plan"])
        apply_money(c4)
        pct = round(d["fact"] / d["plan"] * 100, 1) if d["plan"] else 0
        ws.cell(row=i, column=5, value=f"{pct}%")
    # Итого
    row = len(DISTRICTS_DATA) + 5
    ws.cell(row=row, column=1, value="ИТОГО").font = Font(bold=True)
    ws.cell(row=row, column=2, value=sum(d["orgs"] for d in DISTRICTS_DATA)).font = Font(bold=True)
    c3 = ws.cell(row=row, column=3, value=sum(d["fact"] for d in DISTRICTS_DATA))
    c3.font = Font(bold=True)
    apply_money(c3)
    c4 = ws.cell(row=row, column=4, value=sum(d["plan"] for d in DISTRICTS_DATA))
    c4.font = Font(bold=True)
    apply_money(c4)
    ws.column_dimensions['A'].width = 30
    for col in [2, 3, 4, 5]:
        ws.column_dimensions[get_column_letter(col)].width = 18
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename=districts_{year}.xlsx"})


@router.get("/export/district")
async def export_district(year: int = Query(default=2022), district: str = Query(...)):
    d = next((x for x in DISTRICTS_DATA if x["name"] == district), None)
    if not d:
        d = {"name": district, "fact": 0, "plan": 0, "orgs": 0}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = district[:30]
    ws.merge_cells('A1:C1')
    ws['A1'] = f"Отчёт по району: {district} ({year} год)"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A3'] = "Показатель"
    ws['B3'] = "Значение"
    style_header(ws, 3, 2)
    data = [("Организаций", d["orgs"]), ("ФАКТ, тыс. ₽", d["fact"]), ("ПЛАН, тыс. ₽", d["plan"]),
            ("Освоение", f"{round(d['fact']/d['plan']*100,1)}%" if d['plan'] else "0%")]
    for i, (k, v) in enumerate(data, 4):
        ws.cell(row=i, column=1, value=k)
        c = ws.cell(row=i, column=2, value=v)
        if "тыс" in k:
            apply_money(c)
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 20
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    name = district.replace(' ', '_')[:20]
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={name}_{year}.xlsx"})


@router.get("/export/organization/{org_id}")
async def export_org(org_id: int, year: int = Query(default=2022), quarter: int = Query(default=None)):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчёт"
    headers = ['Наименование', 'ИНН', 'ОКВЭД', 'ОКПО', 'СМП', 'Инвестиции, тыс. ₽']
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    style_header(ws, 1, 6)
    ws.cell(row=2, column=1, value=f"Организация #{org_id}")
    ws.cell(row=2, column=2, value="7200000001")
    c = ws.cell(row=2, column=6, value=5000)
    apply_money(c)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename=org_{org_id}_{year}.xlsx"})


@router.get("/history")
async def get_history():
    return [{"filename": "report_2022.xlsx", "date": datetime.now().strftime("%d.%m.%Y"), "status": "success", "records": 274}]