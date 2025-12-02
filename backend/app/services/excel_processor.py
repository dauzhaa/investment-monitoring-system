import pandas as pd
import io
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Organization, District, InvestmentReport, Okved
from app.models.investment_report import ReportStatus

logger = logging.getLogger(__name__)

def clean_float(val):
    if pd.isna(val): return 0.0
    s = str(val).strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
    if not s or s in ['-', 'nan', 'None', '#REF!', '']: return 0.0
    try:
        return float(s)
    except:
        return 0.0

async def get_or_create_okved(db: AsyncSession, code: str):
    if not code or pd.isna(code): return None
    code_str = str(code).strip()
    
    # Ищем существующий
    stmt = select(Okved).where(Okved.code == code_str)
    res = await db.execute(stmt)
    okved = res.scalar_one_or_none()
    
    if not okved:
        okved = Okved(code=code_str, name=f"ОКВЭД {code_str}")
        db.add(okved)
        await db.commit()
        await db.refresh(okved)
    
    return okved.id

async def process_excel(db: AsyncSession, file_content: bytes, year: int):
    try:
        # Читаем Excel
        df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        
        # Справочник районов
        districts_res = await db.execute(select(District))
        districts_map = {d.name.lower().strip(): d.id for d in districts_res.scalars().all()}

        processed_count = 0

        # Индексы колонок (из твоего файла dop_organizations...):
        # 0: Наименование
        # 1: Район
        # 2: СМП (Да/Нет)
        # 3: ИНН
        # 4: ОКПО
        # 5: ОКВЭД
        # 6: Email
        # 7: Прогноз (Год)
        # 8: 1 кв (янв-март)
        # 9: 2 кв (янв-июнь) - НАКОПИТЕЛЬНО
        # 10: 3 кв (янв-сент) - НАКОПИТЕЛЬНО
        # 11: 4 кв (янв-дек) - НАКОПИТЕЛЬНО
        # 12: Факт Год
        # 13: Причина

        for index, row in df.iterrows():
            try:
                # --- 1. Основные поля ---
                name = str(row.iloc[0]).strip()
                district_raw = str(row.iloc[1]).strip()
                smp_raw = str(row.iloc[2]).strip().lower()
                inn = str(row.iloc[3]).strip().replace('.0', '')
                okved_code = str(row.iloc[5]).strip()
                
                # Валидация ИНН
                if not inn.isdigit() or len(inn) not in [10, 12]:
                    continue

                district_id = districts_map.get(district_raw.lower())
                is_smp = True if 'да' in smp_raw else False
                
                # ОКВЭД
                okved_id = await get_or_create_okved(db, okved_code)

                # --- 2. Организация ---
                stmt = select(Organization).where(Organization.inn == inn)
                res = await db.execute(stmt)
                org = res.scalar_one_or_none()
                
                email = str(row.iloc[6]).split(';')[0].strip() if len(row) > 6 and '@' in str(row.iloc[6]) else None

                if not org:
                    org = Organization(
                        name=name, 
                        inn=inn, 
                        district_id=district_id,
                        okved_id=okved_id,
                        is_smp=is_smp,
                        contact_email=email
                    )
                    db.add(org)
                    await db.commit()
                    await db.refresh(org)
                else:
                    # Обновляем данные
                    updated = False
                    if district_id and org.district_id != district_id:
                        org.district_id = district_id
                        updated = True
                    if okved_id and org.okved_id != okved_id:
                        org.okved_id = okved_id
                        updated = True
                    if email and not org.contact_email:
                        org.contact_email = email
                        updated = True
                    if updated:
                        db.add(org)
                        await db.commit()

                # --- 3. Финансы ---
                forecast = clean_float(row.iloc[7])
                f_q1 = clean_float(row.iloc[8])
                f_q2 = clean_float(row.iloc[9])
                f_q3 = clean_float(row.iloc[10])
                f_q4 = clean_float(row.iloc[11])
                f_annual = clean_float(row.iloc[12])
                
                reason = str(row.iloc[13]).strip() if len(row) > 13 else None
                if reason and reason.lower() in ['nan', 'none', '-']: reason = None

                # Логика статуса
                status = ReportStatus.OVERDUE.value
                if f_annual > 0:
                    status = ReportStatus.SUBMITTED.value
                elif forecast == 0 and f_annual == 0:
                    status = ReportStatus.NOT_PLANNED.value
                elif year < 2025 and forecast == 0:
                     status = ReportStatus.NOT_PLANNED.value

                # --- 4. Отчет ---
                rep_stmt = select(InvestmentReport).where(
                    and_(InvestmentReport.organization_id == org.id, InvestmentReport.year == year)
                )
                report = (await db.execute(rep_stmt)).scalar_one_or_none()

                if not report:
                    report = InvestmentReport(
                        organization_id=org.id,
                        year=year,
                        forecast_annual=forecast,
                        fact_q1=f_q1, fact_q2=f_q2, fact_q3=f_q3, fact_q4=f_q4,
                        fact_annual=f_annual,
                        status=status,
                        comment=reason
                    )
                    db.add(report)
                else:
                    report.forecast_annual = forecast
                    report.fact_q1 = f_q1
                    report.fact_q2 = f_q2
                    report.fact_q3 = f_q3
                    report.fact_q4 = f_q4
                    report.fact_annual = f_annual
                    report.status = status
                    report.comment = reason
                    db.add(report)
                
                await db.commit()
                processed_count += 1

            except Exception as e:
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return {"status": "error", "detail": str(e)}