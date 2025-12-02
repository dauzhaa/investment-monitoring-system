import pandas as pd
import io
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models import Organization, District, InvestmentReport
from app.models.investment_report import ReportStatus

logger = logging.getLogger(__name__)

async def process_excel(db: AsyncSession, file_content: bytes, year: int):
    try:
        # Читаем Excel
        df = pd.read_excel(io.BytesIO(file_content), dtype=str)
        
        # Очищаем названия колонок от лишних пробелов
        df.columns = df.columns.str.strip()
        
        processed_count = 0
        
        # Получаем все районы из базы в словарь для быстрого поиска { "имя": id }
        districts_res = await db.execute(select(District))
        districts_map = {d.name.lower().strip(): d.id for d in districts_res.scalars().all()}

        for index, row in df.iterrows():
            try:
                # 1. Считываем данные по колонкам (Судя по вашему CSV)
                # Колонка 0: Наименование
                # Колонка 1: Район
                # Колонка 3: ИНН
                
                name = str(row.iloc[0]).strip()
                district_name = str(row.iloc[1]).strip()
                inn = str(row.iloc[3]).strip().replace('.0', '') # ИНН в 4-й колонке (индекс 3)
                email_raw = str(row.iloc[6]).strip() if len(row) > 6 else None # Email примерно в 7 колонке

                # Проверка валидности ИНН
                if not inn.isdigit() or len(inn) not in [10, 12]:
                    continue

                # 2. Ищем ID района
                district_id = districts_map.get(district_name.lower())
                
                # 3. Обработка Организации
                # Проверяем, есть ли такая организация
                stmt = select(Organization).where(Organization.inn == inn)
                res = await db.execute(stmt)
                org = res.scalar_one_or_none()
                
                if not org:
                    # Создаем новую
                    org = Organization(
                        name=name, 
                        inn=inn, 
                        district_id=district_id,
                        contact_email=email_raw if email_raw and '@' in email_raw else None
                    )
                    db.add(org)
                    await db.commit()
                    await db.refresh(org)
                else:
                    # Обновляем район, если его не было
                    updated = False
                    if district_id and org.district_id != district_id:
                        org.district_id = district_id
                        updated = True
                    if email_raw and '@' in email_raw and not org.contact_email:
                        org.contact_email = email_raw
                        updated = True
                    
                    if updated:
                        db.add(org)
                        await db.commit()

                # 4. Создаем отчет (статус "Не сдан", так как это только план/список)
                rep_stmt = select(InvestmentReport).where(
                    and_(InvestmentReport.organization_id == org.id, InvestmentReport.year == year)
                )
                res_rep = await db.execute(rep_stmt)
                report = res_rep.scalar_one_or_none()

                if not report:
                    report = InvestmentReport(
                        organization_id=org.id, 
                        year=year, 
                        status=ReportStatus.OVERDUE.value # По умолчанию просрочен
                    )
                    db.add(report)
                    await db.commit()

                processed_count += 1

            except Exception as e:
                logger.warning(f"Ошибка в строке {index}: {e}")
                continue

        return {"status": "success", "processed": processed_count}
    except Exception as e:
        logger.error(f"Global processing error: {e}")
        return {"status": "error", "detail": str(e)}