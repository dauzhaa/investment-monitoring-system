# backend/run_forecasts.py
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import Organization
from app.services.ml_service import MLService

async def generate_all_forecasts():
    print("🚀 Запуск массового прогнозирования...")
    async with AsyncSessionLocal() as session:
        # Берем все организации
        result = await session.execute(select(Organization))
        orgs = result.scalars().all()
        
        print(f"Найдено {len(orgs)} организаций. Считаем...")
        
        count = 0
        for org in orgs:
            # Генерируем прогноз для каждой
            await MLService.generate_forecast(org.id, session)
            count += 1
            if count % 10 == 0:
                print(f"Обработано {count}...")
        
        print("✅ Готово! Прогнозы записаны в базу.")

if __name__ == "__main__":
    asyncio.run(generate_all_forecasts())