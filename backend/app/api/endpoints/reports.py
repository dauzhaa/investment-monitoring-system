from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import aiofiles.os
import os
from app.core.config import settings

from app.api.dependencies import get_current_user
from app.models import User
from app.tasks import excel_tasks

router = APIRouter()

@router.post("/upload")
async def upload_file(current_user: User = Depends(get_current_user), file: UploadFile = File()):
    
    file_path = None
    
    file_path = os.path.join(settings.UPLOAD_PATH, file.filename)
        
    content = await file.read()
        
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
            
    excel_tasks.process_excel_task.delay(file_path=file_path, user_id=current_user.id)
        
    return {"status": "File accepted", "detail":"Ваш файл принят в обработку..."}