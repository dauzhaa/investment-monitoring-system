import asyncio
import logging
import os
from datetime import date, datetime
import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.organization import Organization
from app.models.directories import Okved
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.report_submission import ReportSubmission

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPORTS_DIR = "/app/data/reports"

def calculate_deadline(year: int, quarter: int | None) -> date:
    """Расчет дедлайна сдачи отчета"""
    if quarter == 1: return date(year, 4, 20)
    elif quarter == 2: return date(year, 7, 20)
    elif quarter == 3: return date(year, 10, 20)
    elif quarter == 4: return date(year + 1, 2, 8)
    else: return date(year + 1, 4, 1)

def parse_date(date_val) -> date | None:
    if not date_val: return None
    if isinstance(date_val, datetime): return date_val.date()
    if isinstance(date_val, date): return date_val
    if isinstance(date_val, str):
        try: return datetime.strptime(date_val.strip(), "%d.%m.%Y").date()
        except ValueError: return None
    return None

def clean_inn(inn_val) -> str | None:
    if not inn_val: return None
    cleaned = str(inn_val).split('.')[0].strip()
    return cleaned if cleaned.isdigit() else None

async def process_file(file_path: str, year: int, quarter: int | None, db: AsyncSession):
    """Парсинг одного xlsx файла"""
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        row_data = {
            "name": ws["B3"].value,
            "inn": clean_inn(ws["C3"].value),
            "is_smp": str(ws["D3"].value).strip().lower() == "да" if ws["D3"].value else False,
            "okpo": str(ws["E3"].value).split('.')[0] if ws["E3"].value else None,
            "okved_code": str(ws["F3"].value).strip() if ws["F3"].value else None,
            "forecast": float(ws["G3"].value) if ws["G3"].value and str(ws["G3"].value).replace('.','',1).isdigit() else 0.0,
            "amount": float(ws["H3"].value) if ws["H3"].value and str(ws["H3"].value).replace('.','',1).isdigit() else 0.0,
            "submit_date": parse_date(ws["I3"].value),
            "reason": str(ws["J3"].value).strip() if ws["J3"].value else None,
        }
        wb.close()

        if not row_data["inn"]:
            return False

        # --- 1. Поиск организации ---
        org = (await db.execute(select(Organization).where(Organization.inn == row_data["inn"]))).scalar_one_or_none()
        if not org:
            org = Organization(name=str(row_data["name"])[:512], inn=row_data["inn"])
            db.add(org)
            await db.flush()

        # --- 2. ОКВЭД ---
        if row_data["okved_code"]:
            okved_obj = (await db.execute(select(Okved).where(Okved.code == row_data["okved_code"]))).scalar_one_or_none()
            if not okved_obj:
                okved_obj = Okved(code=row_data["okved_code"])
                db.add(okved_obj)
                await db.flush()
            if not org.okved_id:
                org.okved_id = okved_obj.id

        # --- 3. Факты (InvestmentFact) ---
        report_type = 'p2_quarterly' if quarter else 'p2_annual'
        fact = (await db.execute(
            select(InvestmentFact).where(
                InvestmentFact.organization_id == org.id,
                InvestmentFact.year == year,
                InvestmentFact.quarter == quarter,
                InvestmentFact.report_type == report_type
            )
        )).scalar_one_or_none()

        if fact:
            fact.amount = row_data["amount"]
            fact.no_investment_reason = row_data["reason"]
        else:
            db.add(InvestmentFact(
                organization_id=org.id, year=year, quarter=quarter,
                report_type=report_type, amount=row_data["amount"],
                no_investment_reason=row_data["reason"]
            ))

        # --- 4. Прогнозы (InvestmentForecast) ---
        if row_data["forecast"] > 0:
            existing_forecasts = (await db.execute(
                select(InvestmentForecast)
                .where(InvestmentForecast.organization_id == org.id, InvestmentForecast.year == year)
                .order_by(InvestmentForecast.id.desc())
            )).scalars().all()

            if not existing_forecasts:
                db.add(InvestmentForecast(
                    organization_id=org.id, year=year,
                    forecast_amount=row_data["forecast"], forecast_type='initial'
                ))
            else:
                last_forecast = existing_forecasts[0]
                if last_forecast.forecast_amount != row_data["forecast"]:
                    rev_date = row_data["submit_date"] or date.today()
                    
                    # ПРОВЕРКА: есть ли уже уточнение на ЭТУ ЖЕ дату?
                    same_date_forecast = next(
                        (f for f in existing_forecasts if f.forecast_type == 'revised' and f.revision_date == rev_date), 
                        None
                    )
                    
                    if same_date_forecast:
                        # Если есть - просто обновляем сумму
                        same_date_forecast.forecast_amount = row_data["forecast"]
                    else:
                        # Если нет - создаем новую ревизию
                        db.add(InvestmentForecast(
                            organization_id=org.id, year=year,
                            forecast_amount=row_data["forecast"], forecast_type='revised',
                            revision_date=rev_date
                        ))

        # --- 5. Мониторинг (ReportSubmission) ---
        sub_quarter = quarter if quarter else 4
        subm = (await db.execute(
            select(ReportSubmission).where(
                ReportSubmission.organization_id == org.id,
                ReportSubmission.year == year,
                ReportSubmission.quarter == sub_quarter
            )
        )).scalar_one_or_none()

        deadline = calculate_deadline(year, quarter)
        status = 'submitted' if row_data["submit_date"] else 'pending'
        
        days_overdue = 0
        if status == 'pending' and date.today() > deadline:
            status = 'overdue'
            days_overdue = (date.today() - deadline).days
        elif status == 'submitted' and row_data["submit_date"] > deadline:
            days_overdue = (row_data["submit_date"] - deadline).days

        if subm:
            subm.submitted_date = row_data["submit_date"]
            subm.status = status
            subm.days_overdue = days_overdue
        else:
            db.add(ReportSubmission(
                organization_id=org.id, year=year, quarter=sub_quarter,
                deadline_date=deadline, submitted_date=row_data["submit_date"],
                status=status, days_overdue=days_overdue
            ))

        return True
    except Exception as e:
        await db.rollback() # Сбрасываем поломанную транзакцию
        logger.error(f"❌ Ошибка парсинга файла {file_path}: {e}")
        return False

async def run_import():
    if not os.path.exists(REPORTS_DIR):
        logger.error(f"❌ Папка {REPORTS_DIR} не найдена!")
        return

    async with async_session_factory() as db:
        processed_total = 0
        
        for year_folder in sorted(os.listdir(REPORTS_DIR)):
            year_path = os.path.join(REPORTS_DIR, year_folder)
            if not os.path.isdir(year_path) or not year_folder.isdigit():
                continue
            
            year = int(year_folder)
            logger.info(f"📁 Год: {year}")

            for period_folder in sorted(os.listdir(year_path)):
                period_path = os.path.join(year_path, period_folder)
                if not os.path.isdir(period_path):
                    continue

                quarter = None
                if "1кв" in period_folder.lower(): quarter = 1
                elif "2кв" in period_folder.lower(): quarter = 2
                elif "3кв" in period_folder.lower(): quarter = 3
                elif "4кв" in period_folder.lower(): quarter = 4
                elif "год" in period_folder.lower(): quarter = None

                q_name = f"Квартал {quarter}" if quarter else "Годовой"
                logger.info(f"  📂 Обработка: {q_name} ({period_folder})")

                files = [f for f in os.listdir(period_path) if f.endswith('.xlsx') and not f.startswith('~')]
                
                for file_name in files:
                    file_path = os.path.join(period_path, file_name)
                    success = await process_file(file_path, year, quarter, db)
                    if success:
                        processed_total += 1
                    
                    if processed_total % 100 == 0:
                        await db.commit()
                        logger.info(f"    ⏳ Обработано {processed_total} файлов...")

        await db.commit()
        logger.info(f"✅ Импорт успешно завершен! Всего обработано файлов: {processed_total}")

if __name__ == "__main__":
    asyncio.run(run_import())