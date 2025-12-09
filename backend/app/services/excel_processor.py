import pandas as pd
import io
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Organization, District, Okved, InvestmentReport
from app.models.investment_report import ReportStatus

logger = logging.getLogger(__name__)

def clean_float(val, multiply_by_1000: bool = True):
    if pd.isna(val) or str(val).strip() in ['-', '', 'nan', 'None', '#REF!', 'NaN']:
        return 0.0
    try:
        cleaned = str(val).replace(' ', '').replace(',', '.').replace('\xa0', '').replace(' ', '')
        result = float(cleaned)
        if multiply_by_1000:
            result = result * 1000
        return result
    except:
        return 0.0

def clean_inn(val):
    if pd.isna(val):
        return None
    inn = str(val).strip().replace('.0', '').replace(' ', '')
    inn = re.sub(r'[^\d]', '', inn)
    if len(inn) >= 10 and len(inn) <= 12:
        return inn
    return None

def extract_year_from_headers(df):
    for i, row in df.head(5).iterrows():
        row_str = ' '.join([str(x) for x in row.values])
        match = re.search(r'20(2[2-9]|3[0-9])', row_str)
        if match:
            return int(match.group(0))
    return None

async def process_excel(db: AsyncSession, file_content: bytes, year: int = None):
    try:
        try:
            df = pd.read_excel(io.BytesIO(file_content), header=None)
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_content), header=None, sep=',', encoding='utf-8')
            except Exception:
                df = pd.read_csv(io.BytesIO(file_content), header=None, sep=';', encoding='cp1251')

        logger.info(f"Загружено строк: {len(df)}, столбцов: {len(df.columns)}")
        if year is None:
            year = extract_year_from_headers(df)
            if year is None:
                year = datetime.now().year
                logger.warning(f"Год не определен, используем текущий: {year}")
        
        logger.info(f"Обработка данных за {year} год")
        start_row = 0
        for i, row in df.head(10).iterrows():
            inn_val = clean_inn(row.iloc[3] if len(row) > 3 else None)
            if inn_val:
                start_row = i
                break
        
        if start_row > 0:
            df = df.iloc[start_row:].reset_index(drop=True)
        
        logger.info(f"Данные начинаются со строки {start_row}, осталось строк: {len(df)}")

        processed_count = 0
        errors_count = 0

        for index, row in df.iterrows():
            try:
                if len(row) < 7:
                    continue

                inn = clean_inn(row.iloc[3])
                if not inn:
                    continue

                name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else f"Организация {inn}"
                district_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else None
                is_smp = 'да' in str(row.iloc[2]).lower() if pd.notna(row.iloc[2]) else False
                okved_code = str(row.iloc[5]).strip() if len(row) > 5 and pd.notna(row.iloc[5]) else None
                email = str(row.iloc[6]).strip() if len(row) > 6 and pd.notna(row.iloc[6]) else None
                
                if email and '@' not in email:
                    email = None
                if email and ';' in email:
                    email = email.split(';')[0].strip()

                district = None
                if district_name and district_name.lower() not in ['nan', 'none', '']:
                    res = await db.execute(select(District).where(District.name == district_name))
                    district = res.scalar_one_or_none()
                    
                    if not district:
                        district = District(name=district_name)
                        db.add(district)
                        await db.flush()

                okved = None
                if okved_code and okved_code.lower() not in ['nan', 'none', '']:
                    okved_code = str(okved_code).replace(' ', '')
                    res = await db.execute(select(Okved).where(Okved.code == okved_code))
                    okved = res.scalar_one_or_none()
                    
                    if not okved:
                        okved = Okved(code=okved_code)
                        db.add(okved)
                        await db.flush()

                res = await db.execute(select(Organization).where(Organization.inn == inn))
                org = res.scalar_one_or_none()
                
                if not org:
                    org = Organization(
                        name=name,
                        inn=inn,
                        district_id=district.id if district else None,
                        okved_id=okved.id if okved else None,
                        is_smp=is_smp,
                        contact_email=email
                    )
                    db.add(org)
                    await db.flush()
                else:
                    if district and not org.district_id:
                        org.district_id = district.id
                    if okved and not org.okved_id:
                        org.okved_id = okved.id
                    if email and not org.contact_email:
                        org.contact_email = email

                res = await db.execute(
                    select(InvestmentReport).where(
                        InvestmentReport.organization_id == org.id,
                        InvestmentReport.year == year
                    )
                )
                report = res.scalar_one_or_none()

                if not report:
                    report = InvestmentReport(organization_id=org.id, year=year)
                    db.add(report)
                report.forecast_annual = clean_float(row.iloc[7], multiply_by_1000=True) if len(row) > 7 else 0
                report.fact_q1 = clean_float(row.iloc[8], multiply_by_1000=True) if len(row) > 8 else 0
                report.fact_q2 = clean_float(row.iloc[9], multiply_by_1000=True) if len(row) > 9 else 0
                report.fact_q3 = clean_float(row.iloc[10], multiply_by_1000=True) if len(row) > 10 else 0
                report.fact_q4 = clean_float(row.iloc[11], multiply_by_1000=True) if len(row) > 11 else 0
                report.fact_annual = clean_float(row.iloc[12], multiply_by_1000=True) if len(row) > 12 else 0

                if report.fact_annual == 0:
                    report.fact_annual = report.fact_q1 + report.fact_q2 + report.fact_q3 + report.fact_q4

                if report.fact_annual > 0 or report.forecast_annual > 0:
                    report.status = ReportStatus.SUBMITTED.value
                else:
                    report.status = ReportStatus.OVERDUE.value

                processed_count += 1

                if processed_count % 100 == 0:
                    await db.commit()
                    logger.info(f"Обработано {processed_count} записей...")

            except Exception as e:
                errors_count += 1
                logger.error(f"Ошибка в строке {index}: {e}")
                continue

        await db.commit()
        
        logger.info(f"Завершено: обработано {processed_count}, ошибок {errors_count}")
        return {"status": "success", "processed": processed_count, "errors": errors_count, "year": year}

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await db.rollback()
        return {"status": "error", "detail": str(e)}