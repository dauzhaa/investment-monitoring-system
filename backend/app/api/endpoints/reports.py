from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import os
from datetime import datetime
from app.core.config import settings
from app.api.dependencies import get_current_user
from app.models import User
from app.tasks import excel_tasks
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)

@router.post("/upload")
async def upload_file(
    current_user: User = Depends(get_current_user), 
    file: UploadFile = File(...)
):
    try:
        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{current_user.id}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_PATH, unique_filename)
        
        logger.info(f"Uploading file: {file.filename} to {file_path}")
        
        # Read and save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        logger.info(f"File saved successfully, queuing Celery task")
        
        # Queue Celery task
        task = excel_tasks.process_excel_task.delay(
            file_path=file_path, 
            user_id=current_user.id
        )
        
        return {
            "status": "File accepted", 
            "detail": "Ваш файл принят в обработку...",
            "task_id": task.id
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))