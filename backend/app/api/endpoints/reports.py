from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Form
from fastapi.responses import StreamingResponse
import aiofiles
import os
from datetime import datetime, date
from io import BytesIO
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
    left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
    top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
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
YEARLY_DATA = [{"year": 2022, "fact": 390509, "plan": 393401}, {"year": 2023, "fact": 420000, "plan": 410000}, {"year": 2024, "fact": 450000, "plan": 440000}, {"year": 2025, "fact": 384379, "plan": 470000}]

DISTRICTS_DATA = [
    {"name": "г. Тюмень", "fact": 169154, "plan": 170000, "orgs": 89}, {"name": "Тюменский район", "fact": 51465, "plan": 52000, "orgs": 28},
    {"name": "г. Ишим", "fact": 22902, "plan": 23000, "orgs": 12}, {"name": "г. Тобольск", "fact": 19551, "plan": 20000, "orgs": 18}
]

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), report_type: str = Form(default="annual"), year: int = Form(default=None)):
    if year is None: year = date.today().year
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
    for col, h in enumerate(headers, 1): ws.cell(row=1, column=col, value=h)
    style_header(ws, 1, len(headers))
    ws.cell(row=2, column=1, value='ООО "Пример"')
    ws.cell(row=2, column=6, value=1000)
    apply_money(ws.cell(row=2, column=6))
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=template_{report_type}.xlsx"})

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
    for col, h in enumerate(headers, 1): ws.cell(row=4, column=col, value=h)
    style_header(ws, 4, 4)
    for i, d in enumerate(YEARLY_DATA, 5):
        ws.cell(row=i, column=1, value=d["year"])
        apply_money(ws.cell(row=i, column=2, value=d["fact"]))
        apply_money(ws.cell(row=i, column=3, value=d["plan"]))
        ws.cell(row=i, column=4, value=f"{round(d['fact']/d['plan']*100,1) if d['plan'] else 0}%")
    for col in [1, 2, 3, 4]: ws.column_dimensions[get_column_letter(col)].width = 20
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=yearly_2022-2025.xlsx"})

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
    for col, h in enumerate(headers, 1): ws.cell(row=4, column=col, value=h)
    style_header(ws, 4, 5)
    for i, d in enumerate(DISTRICTS_DATA, 5):
        ws.cell(row=i, column=1, value=d["name"])
        ws.cell(row=i, column=2, value=d["orgs"])
        apply_money(ws.cell(row=i, column=3, value=d["fact"]))
        apply_money(ws.cell(row=i, column=4, value=d["plan"]))
        ws.cell(row=i, column=5, value=f"{round(d['fact']/d['plan']*100,1) if d['plan'] else 0}%")
    ws.column_dimensions['A'].width = 30
    for col in [2, 3, 4, 5]: ws.column_dimensions[get_column_letter(col)].width = 18
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=districts_{year}.xlsx"})

@router.get("/export/district")
async def export_district(year: int = Query(default=2022), district: str = Query(...)):
    d = next((x for x in DISTRICTS_DATA if x["name"] == district), {"name": district, "fact": 0, "plan": 0, "orgs": 0})
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = district[:30]
    ws.merge_cells('A1:C1')
    ws['A1'] = f"Отчёт по району: {district} ({year} год)"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A3'], ws['B3'] = "Показатель", "Значение"
    style_header(ws, 3, 2)
    data = [("Организаций", d["orgs"]), ("ФАКТ, тыс. ₽", d["fact"]), ("ПЛАН, тыс. ₽", d["plan"]), ("Освоение", f"{round(d['fact']/d['plan']*100,1)}%" if d['plan'] else "0%")]
    for i, (k, v) in enumerate(data, 4):
        ws.cell(row=i, column=1, value=k)
        c = ws.cell(row=i, column=2, value=v)
        if "тыс" in k: apply_money(c)
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 20
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={district[:20]}_{year}.xlsx"})

@router.get("/history")
async def get_history():
    return [{"filename": "report_2022.xlsx", "date": datetime.now().strftime("%d.%m.%Y"), "status": "success", "records": 274}]