from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user

# Импортируем наш боевой сервис
from app.services.notification_service import send_real_email

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationCreate(BaseModel):
    organization_id: int
    message: str

@router.post("/send")
async def send_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Только администратор")

    # 1. Сохраняем уведомление в базу (чтобы оно появилось в "колокольчике")
    new_notif = Notification(organization_id=data.organization_id, message=data.message)
    db.add(new_notif)

    # 2. Пишем в Аудит
    audit_entry = AuditLog(
        user_id=current_user.id, action="send_reminder", entity_type="notification",
        details={"target_org_id": data.organization_id, "message": data.message}
    )
    db.add(audit_entry)

    # 3. Ищем Email представителя организации для реальной отправки
    stmt = select(User.email).where(User.organization_id == data.organization_id)
    org_email = (await db.execute(stmt)).scalar_one_or_none()

    if org_email:
        # 4. Отправляем РЕАЛЬНОЕ письмо (асинхронно, не блокируя сервер)
        subject = "Новое уведомление от ИнвестМонитор72"
        await send_real_email(email_to=org_email, subject=subject, body=data.message)

    await db.commit()
    return {"status": "success"}

@router.get("/")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Здесь небольшая логическая ошибка в твоем коде!
    # Нужно фильтровать по current_user.organization_id, а не по current_user.id
    if not current_user.organization_id:
        return [] # У админа нет organization_id
        
    stmt = select(Notification).where(
        Notification.organization_id == current_user.organization_id
    ).order_by(desc(Notification.created_at))
    
    result = await db.execute(stmt)
    return result.scalars().all()