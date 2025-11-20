from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ml_service import MLService
from sqlalchemy import select, func
from app.models import Organization, InvestmentReport, Forecast # <-- Добавили Forecast

router = APIRouter()

# --- ЛОГИКА ДЛЯ КАРТЫ И ML ---

@router.post("/calculate/clustering")
async def calculate_clusters(db: AsyncSession = Depends(get_db)):
    return await MLService.perform_clustering(db)

@router.get("/map")
async def get_map_data(db: AsyncSession = Depends(get_db)):
    stmt = select(Organization.municipality, Organization.cluster_group).where(Organization.municipality.is_not(None))
    res = await db.execute(stmt)
    data = {}
    for row in res.all():
        if row[0]:
            data[row[0]] = row[1] if row[1] is not None else 1 
    return data

# --- ЛОГИКА ДЛЯ ДАШБОРДА (ГЛАВНАЯ) ---

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # 1. Суммы
    sum_query = select(func.sum(InvestmentReport.total_investment))
    total_invest = (await db.execute(sum_query)).scalar() or 0
    
    # 2. Количество орг
    count_query = select(func.count(Organization.id))
    org_count = (await db.execute(count_query)).scalar() or 0
    
    # 3. Диаграмма
    fed = (await db.execute(select(func.sum(InvestmentReport.budget_federal)))).scalar() or 0
    reg = (await db.execute(select(func.sum(InvestmentReport.budget_regional)))).scalar() or 0
    own = (await db.execute(select(func.sum(InvestmentReport.own_funds)))).scalar() or 0

    # 4. Аномалии
    avg_query = select(func.avg(InvestmentReport.total_investment))
    avg_invest = (await db.execute(avg_query)).scalar() or 1
    
    anomalies_query = select(
        Organization.name, 
        InvestmentReport.total_investment,
        InvestmentReport.quarter,
        InvestmentReport.report_year
    ).join(Organization).order_by(InvestmentReport.total_investment.desc()).limit(5)
    
    anomalies_res = await db.execute(anomalies_query)
    anomalies_list = []
    
    for row in anomalies_res.all():
        amount = row[1]
        ratio = amount / avg_invest
        reason = "Высокий расход"
        type_status = "warning"
        
        if ratio > 10:
            reason = f"Превышение среднего в {ratio:.1f} раз"
            type_status = "critical"
        elif ratio > 5:
            reason = f"Выше нормы в {ratio:.1f} раз"
            
        anomalies_list.append({
            "org_name": row[0],
            "amount": f"{amount:,.0f}", 
            "period": f"{row[3]} Q{row[2]}",
            "type": type_status,
            "reason": reason
        })

    return {
        "total_investment": round(total_invest / 1_000_000, 1),
        "org_count": org_count,
        "execution_rate": 87.5, 
        "data_quality": 98, 
        "pie_chart": [
            {"value": round(fed/1000000, 1), "name": "Федеральный"},
            {"value": round(reg/1000000, 1), "name": "Областной"},
            {"value": round(own/1000000, 1), "name": "Внебюджет"}
        ],
        "anomalies": anomalies_list
    }

# --- ЛОГИКА ДЛЯ СТРАНИЦЫ АНАЛИТИКИ (НОВОЕ) ---

@router.get("/trends")
async def get_global_trends(db: AsyncSession = Depends(get_db)):
    """
    Данные для страницы Аналитика:
    1. История (линия)
    2. Прогноз (пунктир)
    3. Топ районов (столбики)
    """
    
    # 1. ИСТОРИЯ (Группируем по годам)
    hist_query = select(
        InvestmentReport.report_year,
        func.sum(InvestmentReport.total_investment)
    ).group_by(InvestmentReport.report_year).order_by(InvestmentReport.report_year)
    
    hist_res = await db.execute(hist_query)
    history = [{"year": row[0], "amount": row[1]} for row in hist_res.all()]

    # 2. ПРОГНОЗ (Группируем по датам прогноза)
    forecast_query = select(
        Forecast.forecast_date,
        func.sum(Forecast.predicted_amount),
        func.sum(Forecast.lower_bound),
        func.sum(Forecast.upper_bound)
    ).group_by(Forecast.forecast_date).order_by(Forecast.forecast_date)
    
    forecast_res = await db.execute(forecast_query)
    forecast = [{
        "date": row[0], 
        "amount": row[1],
        "lower": row[2],
        "upper": row[3]
    } for row in forecast_res.all()]

    # 3. РЕЙТИНГ РАЙОНОВ (Топ-10)
    rating_query = select(
        Organization.municipality,
        func.sum(InvestmentReport.total_investment).label("total")
    ).join(InvestmentReport).group_by(Organization.municipality).order_by(func.sum(InvestmentReport.total_investment).desc()).limit(10)
    
    rating_res = await db.execute(rating_query)
    rating = [{"name": row[0], "value": row[1]} for row in rating_res.all() if row[0]]

    return {
        "history": history,
        "forecast": forecast,
        "rating": rating
    }