from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import aiofiles.os
import os
from app.core.config import settings

from app.api.dependencies import get_current_user
from app.models import User
from app.core.database import get_db
from app.services import excel_processor

router = APIRouter()

@router.POST("/upload")
async def upload_file(current_user: User = Depends(get_current_user), file: UploadFile = File(), db: AsyncSession = Depends(get_db)):
    
    file_path = None
    
    try:
        file_path = os.path.join(settings.UPLOAD_PATH, file.filename)
        
        content = await file.read()
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
            
        reports_list = await excel_processor.process_excel(db=db, file_path=file_path, current_user=current_user)
        
        return reports_list
            
    finally:
        if file_path:
            if await aiofiles.os.path.exists(file_path):
                await aiofiles.os.remove(file_path)