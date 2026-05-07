from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services import analytics_center as service
from app.schemas.analytics_center import (
    DistrictsDispersionResponse,
    PeersResponse,
    DistrictsClustersResponse,
)

router = APIRouter(prefix="/analytics-center", tags=["Analytics Center"])


@router.get("/districts-dispersion", response_model=DistrictsDispersionResponse)
async def get_districts_dispersion(
    year: int = Query(2024, ge=2022, le=2030),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Карта дисциплины региона: box-plot ИПО по районам + ICC.
    Показывает, насколько ИПО зависит от принадлежности к району.
    """
    return await service.calculate_districts_dispersion(db, year)


@router.get("/peers/{organization_id}", response_model=PeersResponse)
async def get_peers(
    organization_id: int,
    year: int = Query(2024, ge=2022, le=2030),
    n: int = Query(7, ge=3, le=15),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Похожие организации для бенчмарка.
    Подбирает N организаций, наиболее близких по категории, ОКВЭД,
    району и размеру плана. Имена похожих не возвращаются — только агрегаты.
    """
    result = await service.find_peers(db, organization_id, year, n)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Не найдено данных для организации id={organization_id} за {year} год"
        )
    return result


@router.get("/districts-clusters", response_model=DistrictsClustersResponse)
async def get_districts_clusters(
    year: int = Query(2024, ge=2022, le=2030),
    n_clusters: int = Query(4, ge=2, le=6),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Кластеризация районов Тюменской области.
    K-means по 4 признакам: avg_ipo, avg_late_days, smp_share, median_plan.
    Возвращает 4 типологических группы с осмысленными именами.
    """
    return await service.cluster_districts(db, year, n_clusters)