import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.database import AsyncSessionLocal  # ИЗМЕНЕНО ЗДЕСЬ
from app.models.directories import District
from app.models.organization import Organization

DISTRICT_ALIASES = {
    'Сорокинский район': 'Сорокинский',
    'Голышмановский район': 'Голышмановский',
    'Викуловский район': 'Викуловский',
    'Аромашевский район': 'Аромашевский',
    'Абатский район': 'Абатский',
    'Сладковский район': 'Сладковский',
    'Нижнетавдинский район': 'Нижнетавдинский',
    'Бердюжский район': 'Бердюжский',
    'Казанский район': 'Казанский',
    'Тобольский район': 'Тобольский',
    'Ишимский район': 'Ишимский',
    'Упоровский район': 'Упоровский',
    'Ялуторовский район': 'Ялуторовский',
    'Омутинский район': 'Омутинский',
    'Юргинский район': 'Юргинский',
    'Уватский район': 'Уватский',
    'Вагайский район': 'Вагайский',
    'Ярковский район': 'Ярковский',
    'Тюменский район': 'Тюменский'
}

async def merge_districts():
    async with AsyncSessionLocal() as db:  # ИЗМЕНЕНО ЗДЕСЬ
        for bad_name, good_name in DISTRICT_ALIASES.items():
            # Ищем правильный район
            good_res = await db.execute(select(District).where(District.name == good_name))
            good_dist = good_res.scalars().first()
            
            # Ищем район с "припиской"
            bad_res = await db.execute(select(District).where(District.name == bad_name))
            bad_dist = bad_res.scalars().first()
            
            if good_dist and bad_dist:
                print(f"Слияние: '{bad_name}' -> '{good_name}'")
                # Переносим организации
                await db.execute(
                    update(Organization)
                    .where(Organization.district_id == bad_dist.id)
                    .values(district_id=good_dist.id)
                )
                # Удаляем дубликат
                await db.execute(delete(District).where(District.id == bad_dist.id))
        
        await db.commit()
        print("Очистка успешно завершена!")

if __name__ == "__main__":
    asyncio.run(merge_districts())