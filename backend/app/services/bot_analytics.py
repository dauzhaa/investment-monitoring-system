from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.models.directories import District

class BotAnalyticsService:
    """Аналитические функции, доступные боту через function calling."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_district_info(self, district_name: str) -> dict:
        """Возвращает информацию о количестве организаций в указанном районе."""
        # Ищем район
        dist_res = await self.db.execute(select(District).where(District.name == district_name))
        district = dist_res.scalars().first()
        
        if not district:
            return {"error": f"Район '{district_name}' не найден в базе данных."}
            
        # Считаем организации
        count_res = await self.db.execute(
            select(func.count(Organization.id)).where(Organization.district_id == district.id)
        )
        org_count = count_res.scalar() or 0
        
        return {
            "district_name": district.name,
            "total_organizations": org_count,
            "message": f"В районе {district.name} зарегистрировано {org_count} подведомственных организаций."
            
        }
    async def find_similar_organizations(self, org_name: str) -> dict:
        """
        Универсальный метод поиска двойников.
        org_name приходит от GigaChat'а динамически.
        """
        try:
            # 1. Ищем саму организацию в БД (через ilike, чтобы искать по подстроке)
            query = select(Organization).where(Organization.name.ilike(f"%{org_name}%")).limit(1)
            result = await self.db.execute(query)
            target_org = result.scalar_one_or_none()

            if not target_org:
                return {"error": f"Организация с названием, похожим на '{org_name}', не найдена в базе."}

            # 2. Вызываем твой ML-сервис k-NN для поиска двойников 
            # (предположим, у тебя есть функция get_knn_twins(org_id))
            # twins = await ml_service.get_knn_twins(target_org.id, k=3)
            
            # Для примера формируем структуру ответа:
            return {
                "target_organization": target_org.name,
                "category": target_org.category,
                "twins_found": [
                    # Сюда подставишь реальные данные из БД / k-NN
                    {"name": "Пример двойника 1", "similarity_score": "95%", "plan_amount": 500000},
                    {"name": "Пример двойника 2", "similarity_score": "88%", "plan_amount": 480000}
                ]
            }
        except Exception as e:
            return {"error": f"Ошибка при расчете: {str(e)}"}