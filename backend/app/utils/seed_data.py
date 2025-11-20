# backend/app/utils/seed_data.py
import asyncio
import csv
import random
from sqlalchemy import select
# ИЗМЕНЕНИЕ ЗДЕСЬ: Импортируем AsyncSessionLocal вместо async_session_factory
from app.core.database import AsyncSessionLocal 
from app.models import Organization, InvestmentReport, User, Forecast
from passlib.context import CryptContext

# Для красивых координат центров районов
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
    print("🌱 Начинаем посев данных...")
    
    # ИЗМЕНЕНИЕ ЗДЕСЬ: используем AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        # 1. Создаем админа
        admin_email = "admin@obr72.ru"
        existing_admin = await session.execute(select(User).where(User.email == admin_email))
        if not existing_admin.scalar():
            admin = User(
                email=admin_email,
                hashed_password=pwd_context.hash("admin"),
                is_active=True,
                is_superuser=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Админ создан: admin@obr72.ru / admin")

        # 2. Читаем CSV и создаем организации
        organizations_count = 0
        try:
            with open("app/utils/НОВЫЙ_СПИСОК_без_дубликатов.csv", "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get('Наименование предприятия', 'Unknown')
                    inn = row.get('ИНН', '').split('.')[0] # Чистим ИНН от .0
                    
                    if not inn or len(inn) < 5: continue

                    # Определение типа
                    org_type = "Прочее"
                    name_upper = name.upper()
                    if "САД" in name_upper or "ДОУ" in name_upper: org_type = "ДОУ"
                    elif "ШКОЛА" in name_upper or "СОШ" in name_upper: org_type = "Школа"
                    elif "КОЛЛЕДЖ" in name_upper or "ТЕХНИКУМ" in name_upper: org_type = "Колледж"

                    # Рандомный район (с весами - в Тюмени больше всего)
                    mun_names = list(MUNICIPALITIES_COORDS.keys())
                    weights = [0.4, 0.15, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.02, 0.03]
                    municipality = random.choices(mun_names, weights=weights, k=1)[0]
                    
                    # Генерация координат (Центр района + случайный шум)
                    center_lat, center_lon = MUNICIPALITIES_COORDS[municipality]
                    lat = center_lat + random.uniform(-0.05, 0.05)
                    lon = center_lon + random.uniform(-0.05, 0.05)

                    # Проверка дублей
                    existing = await session.execute(select(Organization).where(Organization.inn == inn))
                    if existing.scalar(): continue

                    org = Organization(
                        name=name,
                        inn=inn,
                        contact_email=row.get('Почта'),
                        municipality=municipality,
                        org_type=org_type,
                        coordinates={"lat": lat, "lon": lon}
                    )
                    session.add(org)
                    organizations_count += 1
            
            await session.commit()
            print(f"✅ Загружено {organizations_count} новых организаций.")
            
            # Перезагрузим их из базы, чтобы получить ID
            res = await session.execute(select(Organization))
            db_orgs = res.scalars().all()

            # 3. Генерируем отчеты за 2022, 2023, 2024
            reports_count = 0
            years = [2022, 2023, 2024]
            
            print("📊 Генерируем финансовую историю...")
            for org in db_orgs:
                # Базовая сумма зависит от типа (школы богаче садиков)
                base_budget = 1_000_000 if org.org_type == "Школа" else 300_000
                if org.org_type == "Колледж": base_budget = 5_000_000
                
                # Рандомный множитель для "разнообразия"
                scale_factor = random.uniform(0.5, 2.5) 

                for year in years:
                    for q in [1, 2, 3, 4]:
                        if year == 2024 and q > 3: continue # Будущее не генерим

                        # Сезонность: пики в Q3 (ремонты) и Q4 (закрытие года)
                        season_coeff = 1.0
                        if q == 3: season_coeff = 1.5 
                        if q == 4: season_coeff = 2.0
                        
                        total = base_budget * scale_factor * season_coeff * random.uniform(0.8, 1.2)
                        
                        # Разбивка по источникам
                        fed = total * random.uniform(0.5, 0.8)
                        reg = total * random.uniform(0.1, 0.3)
                        own = total - fed - reg
                        if own < 0: own = 0

                        report = InvestmentReport(
                            organization_id=org.id,
                            report_year=year,
                            quarter=q,
                            status="approved",
                            total_investment=round(total, 2),
                            budget_federal=round(fed, 2),
                            budget_regional=round(reg, 2),
                            own_funds=round(own, 2),
                            data={"generated": True} # Заглушка
                        )
                        session.add(report)
                        reports_count += 1
            
            await session.commit()
            print(f"✅ Сгенерировано финансовых отчетов: {reports_count}")

        except FileNotFoundError:
            print("❌ Файл CSV не найден в папке app/utils/! Проверь путь и имя файла.")
        except Exception as e:
            print(f"❌ Ошибка при генерации: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data())    