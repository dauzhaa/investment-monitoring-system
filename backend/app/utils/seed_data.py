import asyncio
import logging
import os
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import User
from app.core.config import settings
from app.core.security import get_password_hash
from app.services.excel_processor import process_excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    """
    1. Создает администратора.
    2. Автоматически загружает CSV/Excel файлы из папки app/initial_data
    """
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
                # Убрали full_name и role, так как их нет в модели
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.commit()
            logger.info("✅ Администратор создан.")
        else:
            logger.info("👌 Администратор уже существует.")

        # 2. АВТОЗАГРУЗКА ФАЙЛОВ
        # Путь к папке: /app/app/initial_data (внутри контейнера)
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