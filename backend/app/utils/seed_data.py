import asyncio
import logging
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models import User
from app.core.config import settings
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_data():
    """Создает ТОЛЬКО администратора. Никаких фейковых данных."""
    logger.info("🌱 Проверка наличия администратора...")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        user = result.scalar_one_or_none()

        if not user:
            logger.info(f"Создание администратора: {settings.FIRST_SUPERUSER}")
            user = User(
                email=settings.FIRST_SUPERUSER,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="Administrator",
                role="admin",
                is_active=True,
                is_superuser=True
            )
            session.add(user)
            await session.commit()
            logger.info("✅ Администратор создан.")
        else:
            logger.info("👌 Администратор уже существует.")

if __name__ == "__main__":
    asyncio.run(seed_data())