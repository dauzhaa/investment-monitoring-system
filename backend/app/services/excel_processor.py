import pandas as pd
import io
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Organization, District, Okved, InvestmentReport
from app.models.investment_report import ReportStatus

logger = logging.getLogger(__name__)

def clean_float(val):
    if pd.isna(val) or str(val).strip() in ['-', '', 'nan', 'None', '#REF!']: return 0.0
    try:
        cleaned = str(val).replace(' ', '').replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

async def process_excel(db: AsyncSession, file_content: bytes, year: int):
    try:
        # 1. Попытка прочитать как CSV с игнорированием ошибок строк
        # dtype=str важен, чтобы ИНН не превратился в число с плавающей точкой
        try:
            df = pd.read_csv(io.BytesIO(file_content), header=None, dtype=str, on_bad_lines='skip', sep=',')
            # Если разделитель не сработал (мало колонок), пробуем ;
            if df.shape[1] < 2:
                 df = pd.read_csv(io.BytesIO(file_content), header=None, dtype=str, on_bad_lines='skip', sep=';')
        except:
            # Если совсем не CSV, пробуем Excel
            df = pd.read_excel(io.BytesIO(file_content), header=None, dtype=str)

        processed_count = 0
        
        for index, row in df.iterrows():
            try:
                raw_str = str(row.values)
                # Пропускаем служебные строки из логов или заголовки
                if "source:" in raw_str or "Наименование" in raw_str:
                    continue

                # Логика для списка организаций (CSV)
                # Обычно: 0-№, 1-Имя, 2-ИНН, 3-Почта (в твоем файле ИНН часто в 3й колонке, индекс 2)
                
                # Ищем ИНН. Он может быть в 2 или 3 колонке
                inn = None
                name = None
                email = None
                
                # Проходим по ячейкам строки и ищем похожий на ИНН
                for col_idx in range(len(row)):
                    val = str(row.iloc[col_idx]).strip().replace('.0', '')
                    if val.isdigit() and len(val) in [10, 12]:
                        inn = val
                        # Обычно имя перед ИНН
                        if col_idx > 0:
                            name = str(row.iloc[col_idx-1]).strip()
                        # А почта после
                        if col_idx + 1 < len(row):
                            email_raw = str(row.iloc[col_idx+1]).strip()
                            if '@' in email_raw:
                                email = email_raw.split(';')[0].split(',')[0].strip()
                        break
                
                # Если не нашли автоматическим перебором, пробуем жесткие индексы для твоего файла
                if not inn:
                    possible_inn = str(row.iloc[2]).strip().replace('.0', '')
                    if possible_inn.isdigit() and len(possible_inn) in [10, 12]:
                        inn = possible_inn
                        name = str(row.iloc[1]).strip()
                        email_raw = str(row.iloc[3]).strip()
                        email = email_raw if '@' in email_raw else None

                if not inn or not name:
                    continue

                # --- Работа с БД ---
                # 1. Организация
                res = await db.execute(select(Organization).where(Organization.inn == inn))
                org = res.scalar_one_or_none()
                
                if not org:
                    org = Organization(
                        name=name,
                        inn=inn,
                        contact_email=email
                    )
                    db.add(org)
                    await db.commit()
                    await db.refresh(org)
                else:
                    # Обновляем email если есть
                    if email and not org.contact_email:
                        org.contact_email = email
                        db.add(org)
                        await db.commit()

                # 2. Отчет (заглушка "Не сдан", если нет)
                res_rep = await db.execute(select(InvestmentReport).where(
                    and_(InvestmentReport.organization_id == org.id, InvestmentReport.year == year)
                ))
                report = res_rep.scalar_one_or_none()

                if not report:
                    report = InvestmentReport(
                        organization_id=org.id, 
                        year=year, 
                        status=ReportStatus.OVERDUE.value
                    )
                    db.add(report)
                    await db.commit()

                processed_count += 1

            except Exception as e:
                # logger.error(f"Row error: {e}")
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return {"status": "error", "detail": str(e)}