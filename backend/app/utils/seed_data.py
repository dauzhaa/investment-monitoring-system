import asyncio
import csv
import random
from sqlalchemy import select, delete, func
from app.core.database import AsyncSessionLocal
from app.models import Organization, InvestmentReport, User, Forecast
from passlib.context import CryptContext

# Координаты (не меняем)
MUNICIPALITIES_COORDS = {
    "г. Тюмень": (57.1522, 65.5419),
    "Тюменский район": (57.05, 65.40),
    "г. Тобольск": (58.1981, 68.2548),
    "Тобольский район": (58.20, 68.30),
    "г. Ишим": (56.1109, 69.4697),
    "Ишимский район": (56.00, 69.30),
    "г. Ялуторовск": (56.6556, 66.3061),
    "Заводоуковский ГО": (56.50, 66.55),
    "Уватский район": (59.14, 68.90),
    "Вагайский район": (57.93, 69.01)
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_data():
    print("🌱 Начинаем генерацию для НОВОЙ схемы БД...")
    
    async with AsyncSessionLocal() as session:
        # 1. Чистим старое
        await session.execute(delete(InvestmentQuarterly))
        await session.execute(delete(UserOrganization))
        await session.commit()

        # 2. Создаем Админа
        admin_email = "admin@obr72.ru"
        if not (await session.execute(select(User).where(User.email == admin_email))).scalar():
            admin = User(
                email=admin_email,
                hashed_password=pwd_context.hash("admin"),
                role="admin",
                is_active=True
            )
            session.add(admin)
            await session.commit()

        # 3. Загрузка Организаций (если нет)
        count = (await session.execute(select(func.count()).select_from(Organization))).scalar()
        if count == 0:
            try:
                with open("app/utils/НОВЫЙ_СПИСОК_без_дубликатов.csv", "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        inn = row.get('ИНН', '').split('.')[0]
                        if len(inn) < 5: continue
                        
                        municipality = random.choice(list(MUNICIPALITIES_COORDS.keys()))
                        
                        org = Organization(
                            name=row.get('Наименование предприятия'),
                            inn=inn,
                            municipality=municipality,
                            is_active=True
                        )
                        session.add(org)
                await session.commit()
                print("✅ Организации загружены.")
            except FileNotFoundError:
                print("❌ CSV файл не найден.")

        # 4. Генерация КВАРТАЛЬНЫХ ОТЧЕТОВ
        orgs = (await session.execute(select(Organization))).scalars().all()
        print(f"📊 Генерируем отчеты для {len(orgs)} организаций...")

        for org in orgs:
            base = 1000000 # 1 млн база
            for year in [2023, 2024]:
                for q in [1, 2, 3, 4]:
                    amount = base * random.uniform(0.5, 1.5)
                    
                    # 30% что отчет не сдали
                    status = 'submitted' if random.random() > 0.3 else 'not_submitted'
                    
                    report = InvestmentQuarterly(
                        organization_id=org.id,
                        year=year,
                        quarter=q,
                        investment_amount=amount if status == 'submitted' else 0,
                        submission_status=status,
                        report_submitted_date=date(year, q*3, 25) if status == 'submitted' else None,
                        
                        # Фейковая разбивка
                        budget_federal=amount * 0.5,
                        budget_regional=amount * 0.3,
                        own_funds=amount * 0.2
                    )
                    session.add(report)
        
        await session.commit()
        print("✅ Данные успешно обновлены.")

if __name__ == "__main__":
    asyncio.run(seed_data())