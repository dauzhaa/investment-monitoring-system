import pandas as pd
import io
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Organization, District, InvestmentReport
from app.models.investment_report import ReportStatus

logger = logging.getLogger(__name__)

def clean_float(val):
    """Превращает строку '1 059' или '1059,5' в float 1059.5"""
    if pd.isna(val): return 0.0
    s = str(val).strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
    if not s or s in ['-', 'nan', 'None', '#REF!']: return 0.0
    try:
        return float(s)
    except:
        return 0.0

async def process_excel(db: AsyncSession, file_content: bytes, year: int):
    try:
        # Читаем Excel, все как строки, чтобы не потерять лидирующие нули в ИНН
        df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        
        processed_count = 0
        
        # Загружаем справочник районов для сопоставления: { "ишимский район": 5, ... }
        districts_res = await db.execute(select(District))
        districts_map = {d.name.lower().strip(): d.id for d in districts_res.scalars().all()}

        # Пропускаем заголовок (обычно 1-я строка, но pandas сам её берет). 
        # Если заголовки сложные, берем данные по индексам колонок:
        # 0: Наименование, 1: Район, 3: ИНН, 6: Email
        # 7: Прогноз, 8: Q1, 9: Q2, 10: Q3, 11: Q4, 12: Год
        
        for index, row in df.iterrows():
            try:
                # 1. Парсим основные поля
                name = str(row.iloc[0]).strip()
                district_raw = str(row.iloc[1]).strip()
                inn = str(row.iloc[3]).strip().replace('.0', '')
                
                # Валидация ИНН
                if not inn.isdigit() or len(inn) not in [10, 12]:
                    continue

                # 2. Ищем ID района
                district_id = districts_map.get(district_raw.lower())
                
                # 3. Создаем или обновляем Организацию
                stmt = select(Organization).where(Organization.inn == inn)
                res = await db.execute(stmt)
                org = res.scalar_one_or_none()
                
                # Email (если есть в 7-й колонке, индекс 6)
                email = str(row.iloc[6]).split(';')[0].strip() if len(row) > 6 and '@' in str(row.iloc[6]) else None

                if not org:
                    org = Organization(
                        name=name, 
                        inn=inn, 
                        district_id=district_id,
                        contact_email=email
                    )
                    db.add(org)
                    await db.commit()
                    await db.refresh(org)
                else:
                    # Обновляем связь с районом и почту если их нет
                    updated = False
                    if district_id and org.district_id != district_id:
                        org.district_id = district_id
                        updated = True
                    if email and not org.contact_email:
                        org.contact_email = email
                        updated = True
                    if updated:
                        db.add(org)
                        await db.commit()

                # 4. Обработка Цифр (Инвестиции)
                forecast = clean_float(row.iloc[7])
                f_q1 = clean_float(row.iloc[8])
                f_q2 = clean_float(row.iloc[9])
                f_q3 = clean_float(row.iloc[10])
                f_q4 = clean_float(row.iloc[11])
                f_annual = clean_float(row.iloc[12])

                # Логика статуса: Если есть годовой факт > 0 -> СДАН, иначе ПРОСРОЧЕН
                status = ReportStatus.SUBMITTED.value if f_annual > 0 else ReportStatus.OVERDUE.value

                # 5. Создаем или обновляем Отчет
                rep_stmt = select(InvestmentReport).where(
                    and_(InvestmentReport.organization_id == org.id, InvestmentReport.year == year)
                )
                report = (await db.execute(rep_stmt)).scalar_one_or_none()

                if not report:
                    report = InvestmentReport(
                        organization_id=org.id,
                        year=year,
                        forecast_annual=forecast,
                        fact_q1=f_q1,
                        fact_q2=f_q2,
                        fact_q3=f_q3,
                        fact_q4=f_q4,
                        fact_annual=f_annual,
                        status=status
                    )
                    db.add(report)
                else:
                    # Обновляем существующий отчет
                    report.forecast_annual = forecast
                    report.fact_q1 = f_q1
                    report.fact_q2 = f_q2
                    report.fact_q3 = f_q3
                    report.fact_q4 = f_q4
                    report.fact_annual = f_annual
                    report.status = status
                    db.add(report)
                
                await db.commit()
                processed_count += 1

            except Exception as e:
                # logger.warning(f"Row error: {e}")
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"Global processing error: {e}")
        return {"status": "error", "detail": str(e)}