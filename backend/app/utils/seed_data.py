import asyncio
import logging
import os
import json
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import User, District # <--- Добавили District
from app.core.config import settings
from app.core.security import hash_password as get_password_hash
from app.services.excel_processor import process_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_districts(session):
    """Заполняет таблицу районов из GeoJSON или жесткого списка"""
    districts_list = [
        "Абатский район", "Армизонский район", "Аромашевский район", 
        "Бердюжский район", "Вагайский район", "Викуловский район", 
        "Голышмановский район", "Заводоуковский район", "Заводоуковск", # Часто бывает отдельно
        "Исетский район", "Ишим", "Ишимский район", 
        "Казанский район", "Нижнетавдинский район", "Омутинский район", 
        "Сладковский район", "Сорокинский район", "Тобольск", 
        "Тобольский район", "Тюменский район", "Тюмень", 
        "Уватский район", "Упоровский район", "Юргинский район", 
        "Ялуторовский район", "Ялуторовск", "Ярковский район"
    ]
    
    logger.info("🗺 Проверка справочника районов...")
    for dist_name in districts_list:
        stmt = select(District).where(District.name == dist_name)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if not existing:
            new_dist = District(name=dist_name)
            session.add(new_dist)
            logger.info(f"➕ Добавлен район: {dist_name}")
    
    await session.commit()

async def seed_data():
    logger.info("🌱 Начало инициализации данных...")

    async with async_session_factory() as session:
        # 1. АДМИНИСТРАТОР
        result = await session.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        user = result.scalar_one_or_none()

        if not user:
            logger.info(f"Создание администратора: {settings.FIRST_SUPERUSER}")
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.commit()
            logger.info("✅ Администратор создан.")
        
        # 2. РАЙОНЫ (НОВОЕ)
        await seed_districts(session)

        # 3. АВТОЗАГРУЗКА ФАЙЛОВ
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "initial_data")
        
        if not os.path.exists(data_dir):
            logger.warning(f"Папка {data_dir} не найдена. Пропуск автозагрузки.")
            return

        # Словарь: Имя файла -> Год отчета
        files_to_load = {
            "2022.csv": 2022,
            "2023.csv": 2023,
            "2024.csv": 2024,
            "2025.csv": 2025
        }

        for filename, year in files_to_load.items():
            file_path = os.path.join(data_dir, filename)
            if os.path.exists(file_path):
                logger.info(f"📂 Нашел файл {filename}, начинаю загрузку...")
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    result = await process_excel(session, content, year)
                    logger.info(f"✅ {filename}: Обработано {result.get('processed')} строк.")
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки {filename}: {e}")
            else:
                logger.info(f"Файл {filename} не найден в папке initial_data.")

if __name__ == "__main__":
    asyncio.run(seed_data())