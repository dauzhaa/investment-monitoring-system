import os
import asyncio
from app.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.crud import crud_user
from app.services import excel_processor, notification_service
from app.models import User
import logging

logger = logging.getLogger(__name__)

async def async_process_excel(file_path: str, user_id: int):
    """Async function that does the actual work"""
    async with AsyncSessionLocal() as db:
        user = await crud_user.get_user_by_id(db, user_id=user_id)
        if not user:
            raise Exception("Пользователь не найден")
        
        try:
            await excel_processor.process_excel(
                db=db, 
                file_path=file_path, 
                current_user=user
            )
            await notification_service.send_report_notification(
                email_to=user.email, 
                status="Успех", 
                details="Ваш отчет успешно отправлен"
            )
            return {"status": "success"}
            
        except Exception as ex:
            await notification_service.send_report_notification(
                email_to=user.email, 
                status="Ошибка", 
                details=str(ex)
            )
            raise
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

@celery_app.task
def process_excel_task(file_path: str, user_id: int):
    """Synchronous Celery task that runs the async function"""
    logger.info(f"Starting Excel processing for user {user_id}")
    
    # Run async function in new event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            async_process_excel(file_path, user_id)
        )
        return result
    finally:
        loop.close()