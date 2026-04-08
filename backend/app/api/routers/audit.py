from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("/")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Журнал аудита доступен только админам
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Подтягиваем логи вместе с email пользователя, который совершил действие
    stmt = (
        select(AuditLog)
        .options(joinedload(AuditLog.user)) 
        .order_by(desc(AuditLog.created_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    # Форматируем ответ для фронтенда
    return [
        {
            "id": log.id,
            "user_email": log.user.email if log.user else "Система",
            "action": log.action,
            "entity_type": log.entity_type,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]