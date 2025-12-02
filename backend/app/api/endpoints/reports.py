from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models import User
from app.services.excel_processor import process_excel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    year: Optional[int] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка и обработка Excel файла с данными по инвестициям.
    Год может быть указан явно или определен автоматически из файла.
    """
    try:
        # Проверяем расширение
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="Поддерживаются только файлы .xlsx, .xls, .csv")
        
        logger.info(f"Получен файл: {file.filename}, год: {year}, пользователь: {current_user.email}")
        
        # Читаем содержимое файла
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Файл пустой")
        
        # Обрабатываем файл напрямую (без Celery для простоты)
        result = await process_excel(db, content, year)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("detail", "Ошибка обработки"))
        
        logger.info(f"Файл обработан: {result}")
        
        return {
            "status": "success",
            "message": "Файл успешно обработан",
            "processed": result.get("processed", 0),
            "errors": result.get("errors", 0),
            "year": result.get("year")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))