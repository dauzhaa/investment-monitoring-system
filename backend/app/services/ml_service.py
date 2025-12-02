# backend/app/services/ml_service.py
import pandas as pd
from prophet import Prophet
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Organization, InvestmentReport
import logging

logger = logging.getLogger(__name__)

class MLService:
    
    @staticmethod
    async def generate_forecast(org_id: int, session: AsyncSession):
        """
        Строит прогноз на будущие годы на основе исторических данных.
        Использует forecast_annual из investment_reports.
        """
        query = select(InvestmentReport).where(
            InvestmentReport.organization_id == org_id
        ).order_by(InvestmentReport.year)
        
        result = await session.execute(query)
        reports = result.scalars().all()
        
        if len(reports) < 2:
            logger.warning(f"Org {org_id}: Недостаточно данных для прогноза (минимум 2 года)")
            return None

        # Готовим DataFrame для Prophet
        data = []
        for r in reports:
            if r.fact_annual > 0:  # Используем только годы с фактическими данными
                date_str = f"{r.year}-12-31"  # Конец года
                data.append({
                    'ds': date_str,
                    'y': float(r.fact_annual)
                })
            
        if len(data) < 2:
            logger.warning(f"Org {org_id}: Недостаточно фактических данных")
            return None
            
        df = pd.DataFrame(data)
        
        # Магия Prophet
        try:
            m = Prophet(
                yearly_seasonality=True, 
                daily_seasonality=False, 
                weekly_seasonality=False
            )
            m.fit(df)
            
            # Прогноз на 3 года вперед
            future = m.make_future_dataframe(periods=3, freq='Y')
            forecast = m.predict(future)
            
            # Возвращаем только будущие значения
            forecast_results = []
            future_data = forecast.tail(3)  # Последние 3 года
            
            for _, row in future_data.iterrows():
                yhat = max(0, row['yhat'])  # Не может быть отрицательным
                forecast_results.append({
                    'year': row['ds'].year,
                    'predicted_amount': round(yhat, 2)
                })
            
            return forecast_results
            
        except Exception as e:
            logger.error(f"Prophet error for org {org_id}: {e}")
            return None

    @staticmethod
    async def perform_clustering(session: AsyncSession):
        """
        Кластеризация организаций по объему инвестиций.
        ВНИМАНИЕ: Эта функция не используется, т.к. мы удалили поле cluster_group.
        Оставлена для совместимости.
        """
        logger.warning("Clustering is deprecated - cluster_group field removed from organizations")
        return {"status": "deprecated", "message": "Clustering functionality removed"}