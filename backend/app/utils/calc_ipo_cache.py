import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.investment_forecast import InvestmentForecast
from app.models.investment_fact import InvestmentFact
from app.models.report_submission import ReportSubmission
from app.models.organization_ipo import OrganizationIPO
from app.services.ipo_calculator import IPOCalculator

async def calculate_and_cache_ipo(year: int = 2024):
    db = AsyncSessionLocal()
    try:
        # 1. Получаем все организации
        orgs = (await db.execute(select(Organization))).scalars().all()
        count = 0
        
        for org in orgs:
            # 2. Собираем данные по сдачам отчетов
            subs = (await db.execute(
                select(ReportSubmission)
                .where(ReportSubmission.organization_id == org.id, ReportSubmission.year == year)
            )).scalars().all()
            submissions_list = [
                {"quarter": s.quarter, "days_overdue": s.days_overdue or 0, "status": s.status} 
                for s in subs
            ]
            
# 3. Собираем план (берем первый найденный, если их случайно несколько)
            forecast = (await db.execute(
                select(InvestmentForecast)
                .where(
                    InvestmentForecast.organization_id == org.id, 
                    InvestmentForecast.year == year, 
                    InvestmentForecast.forecast_type == 'первоначальный'
                )
            )).scalars().first()  # <--- ИЗМЕНЕНИЕ ЗДЕСЬ
            plan_amount = float(forecast.forecast_amount) if forecast and forecast.forecast_amount else 0.0
            
            # 4. Собираем факт (если фактов несколько, пока берем первый)
            fact = (await db.execute(
                select(InvestmentFact)
                .where(InvestmentFact.organization_id == org.id, InvestmentFact.year == year)
            )).scalars().first()  # <--- ИЗМЕНЕНИЕ ЗДЕСЬ
            fact_amount = float(fact.amount) if fact and fact.amount else 0.0
            
            # 5. Считаем ИПО за 4 квартал (конец года)
            ipo_result = IPOCalculator.calculate(
                is_smp=org.is_smp,
                year=year,
                current_quarter=4,
                submissions=submissions_list,
                errors_count=0, # Для синтетики пока 0 ошибок валидации
                fact_amount=fact_amount,
                plan_amount=plan_amount
            )
            
            if ipo_result["ipo"] == "-":
                continue
                
            # 6. Сохраняем или обновляем запись в БД
            existing_ipo = (await db.execute(
                select(OrganizationIPO)
                .where(OrganizationIPO.organization_id == org.id, OrganizationIPO.year == year)
            )).scalar_one_or_none()
            
            if existing_ipo:
                existing_ipo.ipo_score = ipo_result["ipo"]
                existing_ipo.d_score = ipo_result["details"]["discipline"]
                existing_ipo.a_score = ipo_result["details"]["quality"]
                existing_ipo.e_score = ipo_result["details"]["execution"]
            else:
                new_ipo = OrganizationIPO(
                    organization_id=org.id,
                    year=year,
                    ipo_score=ipo_result["ipo"],
                    d_score=ipo_result["details"]["discipline"],
                    a_score=ipo_result["details"]["quality"],
                    e_score=ipo_result["details"]["execution"]
                )
                db.add(new_ipo)
            
            count += 1
        
        await db.commit()
        print(f"✅ Успешно рассчитан и сохранен ИПО для {count} организаций за {year} год!")

    except Exception as e:
        await db.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(calculate_and_cache_ipo(2024))