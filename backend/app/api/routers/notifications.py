from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from pydantic import BaseModel
from app.core.database import get_db
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user

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

    new_notif = Notification(organization_id=data.organization_id, message=data.message)
    db.add(new_notif)

    audit_entry = AuditLog(
        user_id=current_user.id, action="send_reminder", entity_type="notification",
        details={"target_org_id": data.organization_id, "message": data.message}
    )
    db.add(audit_entry)

    await db.commit()
    return {"status": "success"}

@router.get("/")
async def get_my_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Notification).where(
        Notification.organization_id == current_user.id
    ).order_by(desc(Notification.created_at))
    result = await db.execute(stmt)
    return result.scalars().all()