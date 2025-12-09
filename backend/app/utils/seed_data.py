import asyncio
import logging
import os
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import User, District
from app.core.config import settings
from app.core.security import hash_password as get_password_hash
from app.services.excel_processor import process_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_districts(session):
    districts_list = [
        "Абатский район", "Армизонский район", "Аромашевский район", 
        "Бердюжский район", "Вагайский район", "Викуловский район", 
        "Голышмановский район", "Заводоуковский район", "Заводоуковск", "г. Заводоуковск",
        "Исетский район", "Ишим", "г. Ишим", "Ишимский район", 
        "Казанский район", "Нижнетавдинский район", "Омутинский район", 
        "Сладковский район", "Сорокинский район", "Тобольск", "г. Тобольск",
        "Тобольский район", "Тюменский район", "Тюмень", "г. Тюмень",
        "Уватский район", "Упоровский район", "Юргинский район", 
        "Ялуторовский район", "Ялуторовск", "г. Ялуторовск", "Ярковский район"
    ]
    
    logger.info("🗺 Создание районов...")
    for dist_name in districts_list:
        stmt = select(District).where(District.name == dist_name)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        
        if not existing:
            session.add(District(name=dist_name))
    
    await session.commit()

async def seed_data():
    logger.info("🌱 Инициализация БД...")

    async with async_session_factory() as session:
        res = await session.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        if not res.scalar_one_or_none():
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True, is_superuser=True
            )
            session.add(user)
            await session.commit()
            logger.info("✅ Админ создан")

        await seed_districts(session)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "initial_data")
        
        files_to_load = {
            "2022.xlsx": 2022,
            "2023.xlsx": 2023,
            "2024.xlsx": 2024,
            "2025.xlsx": 2025
        }

        if os.path.exists(data_dir):
            for filename, year in files_to_load.items():
                file_path = os.path.join(data_dir, filename)
                if os.path.exists(file_path):
                    logger.info(f"📂 Загрузка {filename} за {year} год...")
                    try:
                        with open(file_path, "rb") as f:
                            content = f.read()
                        res = await process_excel(session, content, year)
                        logger.info(f"   -> {res}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка: {e}")
        else:
            logger.warning(f"Папка {data_dir} не найдена!")

if __name__ == "__main__":
    asyncio.run(seed_data())