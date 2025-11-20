# backend/app/services/ml_service.py
import pandas as pd
from prophet import Prophet
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Organization, InvestmentReport, Forecast
import logging

logger = logging.getLogger(__name__)

class MLService:
    
    @staticmethod
    async def generate_forecast(org_id: int, session: AsyncSession):
        """
        Строит прогноз на 4 квартала вперед.
        """
        query = select(InvestmentReport).where(
            InvestmentReport.organization_id == org_id
        ).order_by(InvestmentReport.report_year, InvestmentReport.quarter)
        
        result = await session.execute(query)
        reports = result.scalars().all()
        
        if len(reports) < 4:
            logger.warning(f"Org {org_id}: Недостаточно данных для прогноза")
            return None

        # 2. Готовим DataFrame для Prophet
        data = []
        for r in reports:
            # Превращаем Квартал в Дату (конец квартала)
            month = r.quarter * 3
            # Выбираем последний день месяца
            day = 30 if month in [6, 9] else 31 
            # Февраль не учитываем т.к. кварталы 3,6,9,12
            
            date_str = f"{r.report_year}-{month:02d}-{day}"
            data.append({
                'ds': date_str,
                'y': float(r.total_investment) # Prophet требует float
            })
            
        df = pd.DataFrame(data)
        
        # 3. Магия Prophet
        try:
            # Отключаем лишние сезонности, у нас только годовая важна
            m = Prophet(yearly_seasonality=True, daily_seasonality=False, weekly_seasonality=False)
            m.fit(df)
            
            # Прогноз на 4 периода (квартала)
            future = m.make_future_dataframe(periods=4, freq='Q')
            forecast = m.predict(future)
        except Exception as e:
            logger.error(f"Prophet error for org {org_id}: {e}")
            return None
        
        # 4. Сохраняем в БД
        # Сначала удаляем старый прогноз
        await session.execute(delete(Forecast).where(Forecast.organization_id == org_id))
        
        forecast_results = []
        # Берем последние 4 строки (это будущее)
        future_data = forecast.tail(4)
        
        for _, row in future_data.iterrows():
            # Обрезаем отрицательные значения (инвестиции не могут быть < 0)
            yhat = max(0, row['yhat'])
            yhat_lower = max(0, row['yhat_lower'])
            yhat_upper = max(0, row['yhat_upper'])

            item = Forecast(
                organization_id=org_id,
                forecast_date=row['ds'].date(),
                predicted_amount=round(yhat, 2),
                lower_bound=round(yhat_lower, 2),
                upper_bound=round(yhat_upper, 2),
                meta_info={"model": "Prophet"}
            )
            session.add(item)
            forecast_results.append(item)
            
        await session.commit()
        return forecast_results

    @staticmethod
    async def perform_clustering(session: AsyncSession):
        """
        Кластеризация районов (K-Means).
        """
        # 1. Агрегируем данные: Район -> Сумма Инвестиций
        stmt = select(
            Organization.municipality,
            func.sum(InvestmentReport.total_investment).label("total_money"),
            func.count(Organization.id).label("org_count")
        ).join(InvestmentReport).group_by(Organization.municipality)
        
        result = await session.execute(stmt)
        rows = result.all() # список кортежей
        
        if not rows:
            return {"error": "No data"}
            
        # 2. Готовим данные для Scikit-Learn
        municipalities = []
        features = []
        
        for row in rows:
            mun_name = row[0]
            total_money = float(row[1] or 0)
            count = row[2]
            
            if not mun_name: continue
            
            # Метрика: Средние инвестиции на 1 организацию
            avg_invest = total_money / count if count > 0 else 0
            
            municipalities.append(mun_name)
            features.append([avg_invest]) # Sklearn требует 2D массив
            
        if len(features) < 3:
            return {"error": "Not enough municipalities for clustering"}

        # 3. K-Means
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(features)
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        
        # 4. Определяем цвета (кто Лидер, кто Отстающий)
        # Создаем временный DataFrame чтобы понять среднее по кластерам
        df_res = pd.DataFrame({'label': labels, 'value': [x[0] for x in features]})
        # Сортируем кластеры по возрастанию денег
        cluster_means = df_res.groupby('label')['value'].mean().sort_values()
        
        # cluster_means.index[0] -> Самый бедный (0)
        # cluster_means.index[2] -> Самый богатый (2)
        mapping = {
            cluster_means.index[0]: 0, # Low
            cluster_means.index[1]: 1, # Mid
            cluster_means.index[2]: 2  # High
        }
        
        # 5. Пишем в БД
        results = {}
        for mun, raw_label in zip(municipalities, labels):
            final_cluster = mapping[raw_label]
            results[mun] = final_cluster
            
            # Обновляем организации этого района
            await session.execute(
                update(Organization)
                .where(Organization.municipality == mun)
                .values(cluster_group=final_cluster)
            )
            
        await session.commit()
        return results