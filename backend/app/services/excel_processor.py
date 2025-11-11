from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

from app.core.database import get_db
from app.api.endpoints import reports
from app.models import User
from app.schemas import ReportCreate
from app.crud import crud_report

async def process_excel(db: AsyncSession, file_path: str, current_user: User):
    
    try:
        df = await run_in_threadpool(pd.read_excel, file_path, engine='openpyxl')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Не удалось прочитать Excel-файл {ex}'
        )
        
    created_reports = []
    
    for idx, row in df.iterrows():
        
        try:
            excell_inn = str(row['ИНН']).strip()
            user_inn = str(current_user.organization.inn).strip()
        except KeyError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="В файле отсутствует колонка 'ИНН'")
        
        if excell_inn != user_inn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Строка {idx+1}: ИНН в файла ({excell_inn})'
                        f'не совпадает с ИНН в вайшей организации ({user_inn})'
            )
            
        forecast_column = "Первоначальный прогноз на 2025 год"
        if forecast_column not in row or pd.isna(row[forecast_column]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Строка {idx+1}: Поле '{forecast_column}' не заполнено"
            )

        report_schema = ReportCreate(
            report_year = 2025,
            data = row.to_dict()
        )
        
        new_report = await crud_report.create_report(
            db=db,
            report_in=report_schema,
            user=current_user,
            organization=current_user.organization
        )
        
        created_reports.append(new_report)
        
    return created_reports