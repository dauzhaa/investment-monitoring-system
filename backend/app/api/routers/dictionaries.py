from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.dictionaries import District, Okved

router = APIRouter()


@router.get("/districts")
async def get_districts(db: AsyncSession = Depends(get_db)):
    """
    Список всех районов.
    """
    stmt = select(District).order_by(District.name)
    res = await db.execute(stmt)
    districts = res.scalars().all()
    
    return [{"id": d.id, "name": d.name} for d in districts]


@router.get("/okveds")
async def get_okveds(db: AsyncSession = Depends(get_db)):
    """
    Список всех ОКВЭД.
    """
    stmt = select(Okved).order_by(Okved.code)
    res = await db.execute(stmt)
    okveds = res.scalars().all()
    
    return [{"id": o.id, "code": o.code, "name": o.name} for o in okveds]