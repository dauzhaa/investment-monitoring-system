import asyncio
import logging
import os
from datetime import date, datetime
import openpyxl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.organization import Organization
from app.models.directories import Okved, District
from app.models.investment_fact import InvestmentFact
from app.models.investment_forecast import InvestmentForecast
from app.models.report_submission import ReportSubmission
from app.models.user import User
from app.models.user_credential import UserCredential
from app.core.security import hash_password as get_password_hash
from app.core.config import settings
from pydantic import ValidationError
from app.schemas.excel_import import ExcelRowSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ИЗМЕНЕНО: Теперь папка берется из uploads
REPORTS_DIR = "/app/uploads"

def calculate_deadline(year: int, quarter: int | None) -> date:
    # Согласно регламенту из документа:
    if quarter == 1: return date(year, 4, 20) # за январь-март -> 20 апреля
    elif quarter == 2: return date(year, 7, 20) # за январь-июнь -> 20 июля
    elif quarter == 3: return date(year, 10, 20) # за январь-сентябрь -> 20 октября
    elif quarter == 4 or quarter is None: return date(year + 1, 2, 8) # Годовая П-2 (инвест) -> 8 февраля
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

def safe_parse_float(val) -> float:
    if val is None: return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        cleaned = str(val).replace(" ", "").replace("\xa0", "").replace(",", ".")
        return float(cleaned)
    except ValueError:
        return 0.0

async def seed_districts(session: AsyncSession):
    districts_list = [
        "Абатский район", "Армизонский район", "Аромашевский район", 
        "Бердюжский район", "Вагайский район", "Викуловский район", 
        "Голышмановский район", "Заводоуковский район", "г. Заводоуковск",
        "Исетский район", "г. Ишим", "Ишимский район", 
        "Казанский район", "Нижнетавдинский район", "Омутинский район", 
        "Сладковский район", "Сорокинский район", "г. Тобольск",
        "Тобольский район", "Тюменский район", "г. Тюмень",
        "Уватский район", "Упоровский район", "Юргинский район", 
        "Ялуторовский район", "г. Ялуторовск", "Ярковский район"
    ]
    logger.info("🗺 Инициализация справочника районов...")
    for dist_name in districts_list:
        stmt = select(District).where(District.name == dist_name)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if not existing:
            session.add(District(name=dist_name))
    await session.commit()

async def process_file(file_path: str, year: int, quarter: int | None, db: AsyncSession) -> dict:
    """
    Возвращает словарь: {"success": int, "errors": list}
    """
    results = {"success": 0, "errors": []}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        # Итерируемся по строкам, начиная с 3-й (сохраняем номер строки для логов)
        for row_idx, row in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
            # Пропускаем пустые строки (если нет ни имени, ни ИНН)
            if not row[1] and not row[2]:
                continue

            raw_data = {
                "name": row[1],
                "inn": row[2],
                "is_smp": row[3],
                "okpo": row[4],
                "okved_code": row[5],
                "forecast": row[6],
                "amount": row[7],
                "submit_date": row[8],
                "reason": row[9],
            }

            # 1. СТРОГАЯ ВАЛИДАЦИЯ ЧЕРЕЗ PYDANTIC
            try:
                valid_data = ExcelRowSchema(**raw_data)
            except ValidationError as e:
                # Если данные кривые, собираем красивые ошибки для этой строки
                error_messages = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                results["errors"].append({
                    "row": row_idx,
                    "organization": raw_data.get("name", "Неизвестно"),
                    "issues": error_messages
                })
                continue
            
            if quarter and quarter > 1 and valid_data.amount > 0:
                prev_quarter = quarter - 1
                # Ищем факт за предыдущий квартал
                stmt_prev = select(InvestmentFact.amount).join(Organization).where(
                    Organization.inn == valid_data.inn,
                    InvestmentFact.year == year,
                    InvestmentFact.quarter == prev_quarter,
                    InvestmentFact.report_type == 'p2_quarterly'
                )
                prev_amount = (await db.execute(stmt_prev)).scalar_one_or_none()
                
                if prev_amount is not None and valid_data.amount < prev_amount:
                    results["errors"].append({
                        "row": row_idx,
                        "organization": valid_data.name,
                        "issues": [
                            f"Логическая ошибка: Сумма за {quarter} кв. накопительным итогом ({valid_data.amount}) "
                            f"не может быть меньше суммы за {prev_quarter} кв. ({prev_amount})."
                        ]
                    })
                    continue

            # 2. ЗАПИСЬ В БАЗУ ДАННЫХ (используем уже очищенные valid_data)
            async with db.begin_nested():
                # Организация
                org = (await db.execute(select(Organization).where(Organization.inn == valid_data.inn))).scalar_one_or_none()
                if not org:
                    org = Organization(name=valid_data.name[:512], inn=valid_data.inn, is_smp=valid_data.is_smp)
                    db.add(org)
                    await db.flush()

                # Учетная запись (оставил твою логику генерации)
                org_email = f"info_{valid_data.inn}@obr72.ru"
                user = (await db.execute(select(User).where(User.email == org_email))).scalar_one_or_none()
                if not user:
                    new_user = User(email=org_email, role="organization", organization_id=org.id, is_active=True, is_email_verified=True)
                    db.add(new_user)
                    await db.flush()
                    db.add(UserCredential(user_id=new_user.id, hashed_password=get_password_hash(valid_data.inn)))

                # ОКВЭД
                if valid_data.okved_code:
                    okved_obj = (await db.execute(select(Okved).where(Okved.code == valid_data.okved_code))).scalar_one_or_none()
                    if not okved_obj:
                        okved_obj = Okved(code=valid_data.okved_code)
                        db.add(okved_obj)
                        await db.flush()
                    if not org.okved_id:
                        org.okved_id = okved_obj.id

                # Факты инвестиций
                report_type = 'p2_quarterly' if quarter else 'p2_annual'
                fact = (await db.execute(
                    select(InvestmentFact).where(
                        InvestmentFact.organization_id == org.id, InvestmentFact.year == year,
                        InvestmentFact.quarter == quarter, InvestmentFact.report_type == report_type
                    )
                )).scalar_one_or_none()

                if fact:
                    fact.amount = valid_data.amount
                    fact.no_investment_reason = valid_data.reason
                else:
                    db.add(InvestmentFact(
                        organization_id=org.id, year=year, quarter=quarter,
                        report_type=report_type, amount=valid_data.amount, no_investment_reason=valid_data.reason
                    ))

                # Прогнозы (План)
                if valid_data.forecast > 0:
                    existing_forecasts = (await db.execute(
                        select(InvestmentForecast)
                        .where(InvestmentForecast.organization_id == org.id, InvestmentForecast.year == year)
                    )).scalars().all()
                    if not existing_forecasts:
                        db.add(InvestmentForecast(
                            organization_id=org.id, year=year, forecast_amount=valid_data.forecast, forecast_type='initial'
                        ))

                # Статус сдачи отчета
                sub_quarter = quarter if quarter else 4
                subm = (await db.execute(
                    select(ReportSubmission).where(
                        ReportSubmission.organization_id == org.id, ReportSubmission.year == year, ReportSubmission.quarter == sub_quarter
                    )
                )).scalar_one_or_none()

                deadline = calculate_deadline(year, quarter)
                status = 'submitted' if valid_data.submit_date else 'pending'
                
                days_overdue = 0
                if status == 'pending' and date.today() > deadline:
                    status = 'overdue'
                    days_overdue = (date.today() - deadline).days
                elif status == 'submitted' and valid_data.submit_date > deadline:
                    days_overdue = (valid_data.submit_date - deadline).days

                if subm:
                    subm.submitted_date = valid_data.submit_date
                    subm.status = status
                    subm.days_overdue = days_overdue
                else:
                    db.add(ReportSubmission(
                        organization_id=org.id, year=year, quarter=sub_quarter,
                        deadline_date=deadline, submitted_date=valid_data.submit_date,
                        status=status, days_overdue=days_overdue
                    ))
            
            results["success"] += 1

        wb.close()
        return results
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка чтения файла {file_path}: {e}")
        return {"success": 0, "errors": [{"row": 0, "organization": "Файл", "issues": [str(e)]}]}

async def run_import():
    logger.info("🌱 Инициализация БД и парсинг файлов...")
    
    if not os.path.exists(REPORTS_DIR):
        logger.error(f"❌ Папка {REPORTS_DIR} не найдена!")
        return

    async with async_session_factory() as db:
        # 1. Создаем Админа
        res = await db.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        if not res.scalar_one_or_none():
            admin = User(email=settings.FIRST_SUPERUSER, role="admin", is_active=True, is_email_verified=True)
            db.add(admin)
            await db.flush()
            db.add(UserCredential(user_id=admin.id, hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)))
            await db.commit()
            logger.info("✅ Главный администратор создан")

        # 2. Заполняем справочник районов
        await seed_districts(db)

        # 3. Парсинг Excel
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
                    
                    if processed_total % 50 == 0:
                        await db.commit()
                        logger.info(f"    ⏳ Закоммичено {processed_total} файлов...")

        await db.commit()
        logger.info(f"✅ Импорт успешно завершен! Всего обработано файлов: {processed_total}")

if __name__ == "__main__":
    asyncio.run(run_import())