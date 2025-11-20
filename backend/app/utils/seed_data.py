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
    print("🌱 Начинаем полную генерацию данных (Организации + Отчеты на ~5 млрд)...")
    
    async with AsyncSessionLocal() as session:
        # 1. Очистка старых отчетов (чтобы не дублировать суммы)
        # Организации НЕ удаляем, чтобы не ломать связи, если они есть.
        # Но если база чистая, то и удалять нечего.
        print("🧹 Очистка таблиц отчетов и прогнозов...")
        await session.execute(delete(InvestmentReport))
        await session.execute(delete(Forecast))
        await session.commit()

        # 2. Создаем админа
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
            print("✅ Админ проверен/создан.")

        # 3. Загружаем Организации из CSV (Твой старый надежный код)
        # Сначала проверяем, есть ли они уже
        res_count = await session.execute(select(func.count()).select_from(Organization))
        count = res_count.scalar()
        
        if count == 0:
            print("📂 Организаций нет. Загружаем из CSV...")
            try:
                # Путь внутри контейнера
                with open("app/utils/НОВЫЙ_СПИСОК_без_дубликатов.csv", "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get('Наименование предприятия', 'Unknown')
                        inn = row.get('ИНН', '').split('.')[0] 
                        
                        if not inn or len(inn) < 5: continue

                        org_type = "Прочее"
                        if "САД" in name.upper() or "ДОУ" in name.upper(): org_type = "ДОУ"
                        elif "ШКОЛА" in name.upper() or "СОШ" in name.upper(): org_type = "Школа"
                        elif "КОЛЛЕДЖ" in name.upper() or "ТЕХНИКУМ" in name.upper(): org_type = "Колледж"

                        mun_names = list(MUNICIPALITIES_COORDS.keys())
                        # Веса для реалистичного распределения (Тюмень больше)
                        weights = [0.4, 0.15, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.02, 0.03]
                        municipality = random.choices(mun_names, weights=weights, k=1)[0]
                        
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
                
                await session.commit()
                print("✅ Организации успешно загружены из CSV.")
            except FileNotFoundError:
                print("❌ Файл CSV не найден! Проверьте app/utils/НОВЫЙ_СПИСОК_без_дубликатов.csv")
        else:
             print(f"ℹ️ Организации уже есть в базе ({count} шт). Пропускаем загрузку CSV.")

        # 4. Генерируем отчеты (С НОВЫМИ УМЕНЬШЕННЫМИ СУММАМИ)
        # Берем организации из базы
        res = await session.execute(select(Organization))
        db_orgs = res.scalars().all()

        reports_count = 0
        years = [2022, 2023, 2024]
        
        print(f"📊 Генерируем финансовую историю для {len(db_orgs)} организаций...")
        
        for org in db_orgs:
            # === БЮДЖЕТЫ (Реалистичные, ~5 млрд всего) ===
            if org.org_type == "Школа":
                base = 1_200_000 # 1.2 млн в квартал
            elif org.org_type == "Колледж":
                base = 3_000_000 # 3 млн в квартал
            else: 
                base = 500_000   # Садики
            
            scale = random.uniform(0.7, 1.3)

            for year in years:
                for q in [1, 2, 3, 4]:
                    season = 1.0
                    if q == 1: season = 0.5
                    if q == 4: season = 1.8
                    noise = random.uniform(0.85, 1.15)

                    total = base * scale * season * noise
                    total = round(total, -3)

                    fed = total * 0.7
                    reg = total * 0.25
                    own = total * 0.05
                    
                    report = InvestmentReport(
                        organization_id=org.id,
                        report_year=year,
                        quarter=q,
                        status="submitted", # Влезает в лимит базы
                        total_investment=total,
                        budget_federal=round(fed, 2),
                        budget_regional=round(reg, 2),
                        own_funds=round(own, 2),
                        data={"generated": True}
                    )
                    session.add(report)
                    reports_count += 1
        
        await session.commit()
        print(f"✅ Успешно! Сгенерировано {reports_count} отчетов.")

if __name__ == "__main__":
    asyncio.run(seed_data())