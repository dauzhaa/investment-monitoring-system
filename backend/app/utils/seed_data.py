import asyncio
import csv
import random
from sqlalchemy import select, delete
from app.core.database import AsyncSessionLocal
from app.models import Organization, InvestmentReport, User, Forecast
from passlib.context import CryptContext

# Координаты (оставляем как были)
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
    print("🌱 Начинаем (пере)генерацию данных с бюджетом ~5 млрд...")
    
    async with AsyncSessionLocal() as session:
        # 0. ОЧИСТКА ТАБЛИЦ (Чтобы суммы не дублировались при повторном запуске)
        # Удаляем отчеты и прогнозы, организации оставляем
        await session.execute(delete(InvestmentReport))
        await session.execute(delete(Forecast))
        await session.commit()
        print("🧹 Старые отчеты удалены.")

        # 1. Создаем админа (если нет)
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
            print("✅ Админ проверен.")

        # 2. Загружаем Организации (если их нет)
        # (Этот блок пропустим если организации уже есть, чтобы не дублировать логику)
        res = await session.execute(select(Organization))
        db_orgs = res.scalars().all()
        
        if not db_orgs:
            print("⚠️ Организаций нет в базе! Сначала загрузите их (или CSV файл не прочитался).")
            # Тут должен быть код чтения CSV, но если ты уже запускал - они есть.
            # Если вдруг база пустая - скопируй код чтения CSV из предыдущей версии.
        else:
             print(f"ℹ️ Найдено {len(db_orgs)} организаций. Генерируем отчеты...")

        # 3. Генерируем отчеты (НОВЫЕ ЦИФРЫ)
        reports_count = 0
        years = [2022, 2023, 2024] # Полные 3 года
        
        for org in db_orgs:
            # === НОВЫЕ БАЗОВЫЕ СТАВКИ (Уменьшили в 5 раз) ===
            # Школа: ~250к в квартал -> 1 млн в год
            # Садик: ~100к в квартал -> 400к в год
            base_budget = 250_000 if org.org_type == "Школа" else 100_000
            if org.org_type == "Колледж": base_budget = 1_000_000 # Колледжи богаче
            
            # Множитель масштаба (чтобы у всех было по-разному)
            scale_factor = random.uniform(0.8, 1.5) 

            for year in years:
                for q in [1, 2, 3, 4]:
                    # Убрали "future" проверку, заполняем весь 2024 год полностью
                    
                    # Сезонность: 
                    # 1 кв - мало (закупки)
                    # 2, 3 кв - ремонты (пик)
                    # 4 кв - закрытие года (пик)
                    season_coeff = 1.0
                    if q == 1: season_coeff = 0.6
                    if q == 3: season_coeff = 1.4 
                    if q == 4: season_coeff = 1.8
                    
                    # Шум +/- 20%
                    noise = random.uniform(0.8, 1.2)

                    # Итоговая сумма
                    total = base_budget * scale_factor * season_coeff * noise
                    
                    # Округляем до тысяч
                    total = round(total, -3)

                    # Разбивка по источникам (Примерная)
                    fed = total * random.uniform(0.5, 0.7)
                    reg = total * random.uniform(0.2, 0.3)
                    own = total - fed - reg
                    if own < 0: own = 0

                    report = InvestmentReport(
                        organization_id=org.id,
                        report_year=year,
                        quarter=q,
                        status="submitted", # Все сдали для красивой картинки
                        total_investment=round(total, 2),
                        budget_federal=round(fed, 2),
                        budget_regional=round(reg, 2),
                        own_funds=round(own, 2),
                        data={"generated": True}
                    )
                    session.add(report)
                    reports_count += 1
        
        await session.commit()
        print(f"✅ Сгенерировано {reports_count} отчетов с реалистичными суммами.")

if __name__ == "__main__":
    asyncio.run(seed_data())