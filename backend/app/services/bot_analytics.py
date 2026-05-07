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