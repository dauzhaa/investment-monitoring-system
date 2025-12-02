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
        # Читаем "как есть" (все в строки), игнорируем ошибки структуры
        try:
            # Сначала пробуем CSV с запятой
            df = pd.read_csv(io.BytesIO(file_content), header=None, dtype=str, on_bad_lines='skip', sep=',')
            if df.shape[1] < 2:
                 # Если не вышло, пробуем точку с запятой
                 df = pd.read_csv(io.BytesIO(file_content), header=None, dtype=str, on_bad_lines='skip', sep=';')
        except:
            # Если совсем плохо, пробуем Excel
            df = pd.read_excel(io.BytesIO(file_content), header=None, dtype=str)

        processed_count = 0
        
        for index, row in df.iterrows():
            try:
                raw_str = str(row.values)
                # Пропускаем мусорные строки
                if "source:" in raw_str or "Наименование" in raw_str:
                    continue

                inn = None
                name = None
                email = None
                
                # Ищем ИНН перебором ячеек (он может быть во 2-й или 3-й колонке)
                for i in range(len(row)):
                    val = str(row.iloc[i]).strip().replace('.0', '')
                    # ИНН юрлица 10 цифр, ИП 12 цифр
                    if val.isdigit() and len(val) in [10, 12]:
                        inn = val
                        # Имя обычно перед ИНН
                        if i > 0: name = str(row.iloc[i-1]).strip()
                        # Почта обычно после
                        if i + 1 < len(row): 
                            email_raw = str(row.iloc[i+1]).strip()
                            if '@' in email_raw:
                                email = email_raw.split(';')[0].split(',')[0].strip()
                        break
                
                # Если перебор не сработал, берем жестко по твоей структуре (col 1=Name, col 2=INN)
                if not inn:
                    possible_inn = str(row.iloc[2]).strip().replace('.0', '')
                    if possible_inn.isdigit() and len(possible_inn) in [10, 12]:
                        inn = possible_inn
                        name = str(row.iloc[1]).strip()
                
                if not inn or not name:
                    continue

                # 1. Создаем/Обновляем Организацию
                res = await db.execute(select(Organization).where(Organization.inn == inn))
                org = res.scalar_one_or_none()
                
                if not org:
                    org = Organization(name=name, inn=inn, contact_email=email)
                    db.add(org)
                    await db.commit()
                    await db.refresh(org)
                else:
                    if email and not org.contact_email:
                        org.contact_email = email
                        db.add(org)
                        await db.commit()

                # 2. Создаем пустой отчет (чтобы организация появилась в мониторинге как "Не сдан")
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
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return {"status": "error", "detail": str(e)}