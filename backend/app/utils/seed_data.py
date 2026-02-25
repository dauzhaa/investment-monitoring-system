import asyncio
import logging
import os
import csv
import re
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.user import User
from app.models.user_credential import UserCredential
from app.models.organization import Organization
from app.models.directories import District
from app.core.config import settings
from app.core.security import hash_password as get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_inn(inn_val):
    """Очистка ИНН от .0 и пробелов"""
    if not inn_val:
        return None
    cleaned = str(inn_val).split('.')[0].strip()
    return cleaned if cleaned.isdigit() else None

def extract_emails(email_str):
    """Извлечение списка email из грязной строки"""
    if not email_str or email_str.strip().lower() == "нет в списке дф":
        return []
    # Заменяем запятые на точки с запятой и бьем по ним
    raw_emails = email_str.replace(',', ';').split(';')
    valid_emails = []
    for em in raw_emails:
        em = em.strip().lower()
        # Простая проверка на наличие @ и точки
        if '@' in em and '.' in em and ' ' not in em:
            valid_emails.append(em)
    return list(set(valid_emails)) # Убираем дубликаты

async def seed_districts(session):
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
    
    logger.info("🗺 Создание районов (справочник)...")
    for dist_name in districts_list:
        stmt = select(District).where(District.name == dist_name)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if not existing:
            session.add(District(name=dist_name))
    await session.commit()

async def seed_data():
    logger.info("🌱 Инициализация БД...")

    async with async_session_factory() as session:
        # 1. СОЗДАНИЕ АДМИНА
        res = await session.execute(select(User).where(User.email == settings.FIRST_SUPERUSER))
        if not res.scalar_one_or_none():
            admin = User(
                email=settings.FIRST_SUPERUSER,
                role="admin",
                is_active=True,
                is_email_verified=True
            )
            session.add(admin)
            await session.flush()

            creds = UserCredential(
                user_id=admin.id,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
            )
            session.add(creds)
            await session.commit()
            logger.info("✅ Главный администратор создан")

        # 2. СОЗДАНИЕ СПРАВОЧНИКОВ
        await seed_districts(session)

        # 3. ПАРСИНГ CSV: Организации + Пользователи
        csv_path = os.path.join(os.path.dirname(__file__), "НОВЫЙ_СПИСОК_без_дубликатов.csv")
        if not os.path.exists(csv_path):
            logger.error(f"❌ Файл {csv_path} не найден!")
            return

        logger.info("📂 Чтение CSV и создание организаций с аккаунтами...")
        
        orgs_created = 0
        users_created = 0

        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get("Наименование предприятия", "").strip()
                inn = clean_inn(row.get("ИНН", ""))
                emails_str = row.get("Почта", "")
                
                if not inn:
                    continue
                
                # Ищем или создаем организацию
                org_stmt = select(Organization).where(Organization.inn == inn)
                org = (await session.execute(org_stmt)).scalar_one_or_none()
                
                if not org:
                    org = Organization(name=name[:512], inn=inn, is_smp=False)
                    session.add(org)
                    await session.flush() # Получаем org.id
                    orgs_created += 1
                
                # Обрабатываем почты
                valid_emails = extract_emails(emails_str)
                for email in valid_emails:
                    user_stmt = select(User).where(User.email == email)
                    user = (await session.execute(user_stmt)).scalar_one_or_none()
                    
                    if not user:
                        # Создаем пользователя-респондента
                        new_user = User(
                            email=email,
                            role="organization",
                            organization_id=org.id,
                            is_active=True,
                            is_email_verified=True # Сразу верифицирован для тестов
                        )
                        session.add(new_user)
                        await session.flush()
                        
                        # Даем дефолтный пароль (например, ИНН организации)
                        new_creds = UserCredential(
                            user_id=new_user.id,
                            hashed_password=get_password_hash(inn) 
                        )
                        session.add(new_creds)
                        users_created += 1

                # Коммитим батчами
                if orgs_created % 50 == 0:
                    await session.commit()

        await session.commit()
        logger.info(f"✅ Импорт CSV завершен! Создано организаций: {orgs_created}, пользователей: {users_created}")

if __name__ == "__main__":
    asyncio.run(seed_data())