import pandas as pd
import io
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.dictionaries import District, Okved
from app.models.organization import Organization
from app.models.investment_report import InvestmentReport
import logging

logger = logging.getLogger(__name__)

async def process_excel(db: Session, file_content: bytes, year: int = 2024):
    """
    Парсит CSV/Excel файл согласно новой структуре БД (Сущности/Справочники).
    Предполагается структура CSV как в organizations_invest_2022.xlsx
    """
    try:
        # Пытаемся прочитать как Excel, если ошибка - как CSV
        try:
            df = pd.read_excel(io.BytesIO(file_content), header=None) # Читаем без заголовка сначала
        except:
            # Для русского CSV часто нужен разделитель ; или , и кодировка cp1251 или utf-8
            df = pd.read_csv(io.BytesIO(file_content), sep=',', encoding='utf-8', header=None)

        # Ищем строку заголовка (где есть "ИНН" и "Наименование")
        header_idx = -1
        for i, row in df.head(20).iterrows():
            row_str = row.astype(str).str.cat(sep=' ').lower()
            if 'инн' in row_str and 'наименование' in row_str:
                header_idx = i
                break
        
        if header_idx != -1:
            # Перечитываем с правильным заголовком
            df.columns = df.iloc[header_idx]
            df = df.iloc[header_idx+1:].reset_index(drop=True)
        
        processed_count = 0
        
        # Индексы столбцов (базируемся на твоем CSV):
        # 0: Наименование, 1: Район, 2: СМП, 3: ИНН, 5: ОКВЭД, 6: Email
        # 7: Прогноз, 8: Факт 1кв, 9: Факт 2кв, 10: Факт 3кв, 11: Факт 4кв, 12: Итого год
        
        for index, row in df.iterrows():
            try:
                # Очистка и получение базовых полей
                inn_raw = str(row.iloc[3]).strip().replace('.0', '')
                if not inn_raw or len(inn_raw) < 5 or inn_raw.lower() == 'nan':
                    continue

                name_val = str(row.iloc[0]).strip()
                district_val = str(row.iloc[1]).strip()
                smp_val = str(row.iloc[2]).strip()
                okved_val = str(row.iloc[5]).strip()
                email_val = str(row.iloc[6]).strip()

                # --- 1. Работа со СПРАВОЧНИКАМИ (Dictionaries) ---
                
                # Район
                district = None
                if district_val and district_val.lower() != 'nan':
                    stmt = select(District).where(District.name == district_val)
                    district = db.execute(stmt).scalar_one_or_none()
                    if not district:
                        district = District(name=district_val)
                        db.add(district)
                        db.commit()
                        db.refresh(district)

                # ОКВЭД
                okved = None
                if okved_val and okved_val.lower() != 'nan':
                    stmt = select(Okved).where(Okved.code == okved_val)
                    okved = db.execute(stmt).scalar_one_or_none()
                    if not okved:
                        okved = Okved(code=okved_val)
                        db.add(okved)
                        db.commit()
                        db.refresh(okved)

                # --- 2. Работа с СУЩНОСТЬЮ ОРГАНИЗАЦИЯ (Entity) ---
                stmt = select(Organization).where(Organization.inn == inn_raw)
                org = db.execute(stmt).scalar_one_or_none()

                is_smp_bool = 'да' in smp_val.lower()

                if not org:
                    org = Organization(
                        name=name_val,
                        inn=inn_raw,
                        district_id=district.id if district else None,
                        okved_id=okved.id if okved else None,
                        is_smp=is_smp_bool,
                        email=email_val if '@' in email_val else None
                    )
                    db.add(org)
                    db.commit()
                    db.refresh(org)
                else:
                    # Обновляем данные, если изменились
                    org.district_id = district.id if district else org.district_id
                    org.okved_id = okved.id if okved else org.okved_id
                    org.email = email_val if '@' in email_val else org.email

                # --- 3. Работа с СУЩНОСТЬЮ ОТЧЕТ (InvestmentReport) ---
                
                def clean_float(val):
                    if pd.isna(val) or str(val).strip() == '-': return 0.0
                    try:
                        return float(str(val).replace(' ', '').replace(',', '.'))
                    except:
                        return 0.0

                stmt = select(InvestmentReport).where(
                    InvestmentReport.organization_id == org.id,
                    InvestmentReport.year == year
                )
                report = db.execute(stmt).scalar_one_or_none()

                if not report:
                    report = InvestmentReport(organization_id=org.id, year=year)
                    db.add(report)

                # Заполняем цифры
                report.forecast_annual = clean_float(row.iloc[7])
                report.fact_q1 = clean_float(row.iloc[8])
                report.fact_q2 = clean_float(row.iloc[9])
                report.fact_q3 = clean_float(row.iloc[10])
                report.fact_q4 = clean_float(row.iloc[11])
                report.fact_annual = clean_float(row.iloc[12])

                # Логика статуса (простая)
                if report.fact_annual > 0 or report.fact_q1 > 0:
                    report.status = "Сдан"
                else:
                    report.status = "Не сдан"

                db.commit()
                processed_count += 1

            except Exception as e:
                print(f"Ошибка в строке {index}: {e}")
                continue

        return {"status": "success", "processed": processed_count}

    except Exception as ex:
        print(f"CRITICAL ERROR: {ex}")
        return {"status": "error", "detail": str(ex)}