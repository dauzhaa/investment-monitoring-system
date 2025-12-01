import pandas as pd
import io
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Organization, District, Okved, InvestmentReport

logger = logging.getLogger(__name__)

def clean_float(val):
    if pd.isna(val) or str(val).strip() in ['-', '']: return 0.0
    try:
        # Убираем пробелы (1 000 -> 1000) и меняем запятую на точку
        return float(str(val).replace(' ', '').replace(',', '.'))
    except:
        return 0.0

async def process_excel(db: Session, file_content: bytes, year: int):
    try:
        # Читаем файл. Твои файлы - это CSV с разделителем "," или ";" (судя по Excel экспорту)
        # Попробуем прочитать как Excel, если не выйдет - как CSV
        try:
            df = pd.read_excel(io.BytesIO(file_content), header=None)
        except:
            df = pd.read_csv(io.BytesIO(file_content), header=None, sep=',', encoding='utf-8')

        # Ищем шапку (строку с "ИНН" и "Наименование")
        header_idx = -1
        for i, row in df.head(20).iterrows():
            row_str = row.astype(str).str.cat(sep=' ').lower()
            if 'инн' in row_str and 'наименование' in row_str:
                header_idx = i
                break
        
        if header_idx != -1:
            df = df.iloc[header_idx+1:].reset_index(drop=True)

        processed_count = 0
        
        for index, row in df.iterrows():
            try:
                # Индексы колонок согласно твоим файлам
                inn_raw = str(row.iloc[3]).strip().replace('.0', '')
                if not inn_raw or len(inn_raw) < 5 or 'nan' in inn_raw.lower():
                    continue

                name_val = str(row.iloc[0]).strip()
                district_name = str(row.iloc[1]).strip()
                is_smp = 'да' in str(row.iloc[2]).lower()
                okved_code = str(row.iloc[5]).strip()
                email_val = str(row.iloc[6]).strip()

                # 1. Справочник: Район
                district = None
                if district_name and district_name.lower() != 'nan':
                    district = db.query(District).filter(District.name == district_name).first()
                    if not district:
                        district = District(name=district_name)
                        db.add(district)
                        db.commit()

                # 2. Справочник: ОКВЭД
                okved = None
                if okved_code and okved_code.lower() != 'nan':
                    okved = db.query(Okved).filter(Okved.code == okved_code).first()
                    if not okved:
                        okved = Okved(code=okved_code)
                        db.add(okved)
                        db.commit()

                # 3. Организация
                org = db.query(Organization).filter(Organization.inn == inn_raw).first()
                if not org:
                    org = Organization(
                        name=name_val,
                        inn=inn_raw,
                        district_id=district.id if district else None,
                        okved_id=okved.id if okved else None,
                        is_smp=is_smp,
                        email=email_val if '@' in email_val else None
                    )
                    db.add(org)
                    db.commit()
                else:
                    # Обновляем email и статус если изменились
                    org.email = email_val if '@' in email_val else org.email
                    org.is_smp = is_smp
                    if district: org.district_id = district.id

                # 4. Отчет (InvestmentReport)
                report = db.query(InvestmentReport).filter(
                    InvestmentReport.organization_id == org.id,
                    InvestmentReport.year == year
                ).first()

                if not report:
                    report = InvestmentReport(organization_id=org.id, year=year)
                    db.add(report)

                # Заполняем данными
                report.forecast_annual = clean_float(row.iloc[7])
                report.fact_q1 = clean_float(row.iloc[8])
                report.fact_q2 = clean_float(row.iloc[9])
                report.fact_q3 = clean_float(row.iloc[10])
                report.fact_q4 = clean_float(row.iloc[11])
                report.fact_annual = clean_float(row.iloc[12])

                # Логика статуса
                # Если текущий квартал (например) имеет данные - значит сдан.
                # Для упрощения: если есть Факт за год или Факт Q1 > 0 -> "Сдан", иначе "Не сдан"
                if report.fact_annual > 0 or report.fact_q1 > 0:
                    report.status = "Сдан"
                else:
                    report.status = "Не сдан"

                db.commit()
                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing row {index}: {e}")
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return {"status": "error", "detail": str(e)}