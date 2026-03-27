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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ИЗМЕНЕНО: Теперь папка берется из uploads
REPORTS_DIR = "/app/uploads"

def calculate_deadline(year: int, quarter: int | None) -> date:
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

async def process_file(file_path: str, year: int, quarter: int | None, db: AsyncSession) -> bool:
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        processed_any = False
        
        # Итерируемся по строкам, начиная с 3-й
        for row in ws.iter_rows(min_row=3, values_only=True):
            # Извлекаем данные из колонок: B(1)-Наименование, C(2)-ИНН, D(3)-СМП и т.д.
            name_val = row[1]
            inn_val = clean_inn(row[2])
            
            # Пропускаем пустые строки или строки без корректного ИНН
            if not name_val or not inn_val:
                continue

            row_data = {
                "name": str(name_val).strip(),
                "inn": inn_val,
                "is_smp": str(row[3]).strip().lower() == "да" if row[3] else False,
                "okpo": str(row[4]).split('.')[0] if row[4] else None,
                "okved_code": str(row[5]).strip() if row[5] else None,
                "forecast": safe_parse_float(row[6]),
                "amount": safe_parse_float(row[7]),
                "submit_date": parse_date(row[8]),
                "reason": str(row[9]).strip() if row[9] else None,
            }

            async with db.begin_nested():
                # 1. Организация
                org = (await db.execute(select(Organization).where(Organization.inn == row_data["inn"]))).scalar_one_or_none()
                if not org:
                    org = Organization(name=row_data["name"][:512], inn=row_data["inn"], is_smp=row_data["is_smp"])
                    db.add(org)
                    await db.flush()

                # 2. Учетная запись организации
                org_email = f"info_{row_data['inn']}@obr72.ru"
                user = (await db.execute(select(User).where(User.email == org_email))).scalar_one_or_none()
                if not user:
                    new_user = User(
                        email=org_email, role="organization", organization_id=org.id,
                        is_active=True, is_email_verified=True
                    )
                    db.add(new_user)
                    await db.flush()
                    db.add(UserCredential(user_id=new_user.id, hashed_password=get_password_hash(row_data["inn"])))

                # 3. ОКВЭД
                if row_data["okved_code"]:
                    okved_obj = (await db.execute(select(Okved).where(Okved.code == row_data["okved_code"]))).scalar_one_or_none()
                    if not okved_obj:
                        okved_obj = Okved(code=row_data["okved_code"])
                        db.add(okved_obj)
                        await db.flush()
                    if not org.okved_id:
                        org.okved_id = okved_obj.id

                # 4. Факты инвестиций
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

                # 5. Прогнозы (План)
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

                # 6. Статус сдачи отчета
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
            
            processed_any = True

        wb.close()
        return processed_any
        
    except Exception as e:
        logger.error(f"❌ Ошибка парсинга файла {file_path}: {e}")
        return False

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