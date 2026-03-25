from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("/")
async def get_audit_logs(
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()