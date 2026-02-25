import asyncio
import pandas as pd
import os
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.organization import Organization
from app.models.directories import District

async def enrich_db():
    csv_path = "/app/app/utils/НОВЫЙ_СПИСОК_без_дубликатов.csv"
    
    # 1. Загружаем email-адреса из CSV
    email_dict = {}
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            inn_val = str(row.get('ИНН', '')).split('.')[0].strip()
            # Берем только первый email до точки с запятой
            email_val = str(row.get('Почта', '')).split(';')[0].strip()
            if inn_val and email_val and email_val.lower() != 'nan' and 'нет в списке' not in email_val.lower():
                email_dict[inn_val] = email_val

    async with async_session_factory() as db:
        districts = (await db.execute(select(District))).scalars().all()
        dist_map = {d.name: d.id for d in districts}

        orgs = (await db.execute(select(Organization))).scalars().all()
        
        updated_count = 0
        for org in orgs:
            # Обновляем Email
            if org.inn in email_dict:
                org.contact_email = email_dict[org.inn]

            # Умное определение района по названию
            name_lower = org.name.lower()
            matched_district = "г. Тюмень" # По умолчанию для областных учреждений
            
            # Логика поиска
            if "тюменский район" in name_lower or "богандинск" in name_lower or "боровск" in name_lower or "винзилинск" in name_lower or "каскаринск" in name_lower or "переваловск" in name_lower or "мальковск" in name_lower or "успенск" in name_lower or "московск" in name_lower or "ембаевск" in name_lower or "борковск" in name_lower or "червишевск" in name_lower or "новотарманск" in name_lower:
                matched_district = "Тюменский район"
            elif "г. тюмени" in name_lower or "г.тюмени" in name_lower or "города тюмени" in name_lower:
                matched_district = "г. Тюмень"
            
            elif "ишим" in name_lower:
                matched_district = "г. Ишим" if ("г. ишим" in name_lower or "города ишим" in name_lower) else "Ишимский район"
            elif "тобольск" in name_lower or "аремзянск" in name_lower or "сетовск" in name_lower or "прииртышск" in name_lower:
                matched_district = "г. Тобольск" if ("г. тобольск" in name_lower or "города тобольск" in name_lower) else "Тобольский район"
            elif "ялуторовск" in name_lower or "беркутск" in name_lower:
                matched_district = "г. Ялуторовск" if ("г. ялуторовск" in name_lower or "города ялуторовск" in name_lower) else "Ялуторовский район"
            elif "заводоуковск" in name_lower or "боновинск" in name_lower:
                matched_district = "г. Заводоуковск" if "г. заводоуковск" in name_lower else "Заводоуковский район"
            
            elif "абатск" in name_lower or "банниковск" in name_lower: matched_district = "Абатский район"
            elif "армизон" in name_lower or "южно-дубровинск" in name_lower: matched_district = "Армизонский район"
            elif "аромаш" in name_lower: matched_district = "Аромашевский район"
            elif "бердюж" in name_lower or "окунёво" in name_lower: matched_district = "Бердюжский район"
            elif "вагай" in name_lower or "бегишевск" in name_lower or "осиновск" in name_lower: matched_district = "Вагайский район"
            elif "викулов" in name_lower: matched_district = "Викуловский район"
            elif "голышманов" in name_lower or "малышенск" in name_lower: matched_district = "Голышмановский район"
            elif "исетск" in name_lower or "шороховск" in name_lower or "слобода-бешкильск" in name_lower: matched_district = "Исетский район"
            elif "казанск" in name_lower: matched_district = "Казанский район"
            elif "нижнетавдин" in name_lower: matched_district = "Нижнетавдинский район"
            elif "омутин" in name_lower: matched_district = "Омутинский район"
            elif "сладков" in name_lower: matched_district = "Сладковский район"
            elif "сорокин" in name_lower: matched_district = "Сорокинский район"
            elif "уват" in name_lower or "туртас" in name_lower or "демьянск" in name_lower or "ивановск" in name_lower: matched_district = "Уватский район"
            elif "упоровс" in name_lower or "емуртлин" in name_lower or "суерск" in name_lower or "пятковск" in name_lower or "буньковск" in name_lower: matched_district = "Упоровский район"
            elif "юргинск" in name_lower or "северо-плетневск" in name_lower: matched_district = "Юргинский район"
            elif "ярковск" in name_lower or "аксаринс" in name_lower or "староалександровск" in name_lower: matched_district = "Ярковский район"

            # Назначаем ID района
            if matched_district in dist_map:
                org.district_id = dist_map[matched_district]
            
            updated_count += 1
        
        await db.commit()
        print(f"✅ Успешно обогащено {updated_count} организаций (Email, Район).")

if __name__ == "__main__":
    asyncio.run(enrich_db())