from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.user import User
from app.models.user_session import UserSession
from app.crud.crud_user import get_user_by_id

async def get_current_user(
    session_id: str | None = Cookie(default=None), 
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Не авторизован", 
    )
    
    if not session_id:
        raise credentials_exception

    # Ищем сессию в таблице user_sessions
    stmt = select(UserSession).where(UserSession.session_token == session_id)
    result = await db.execute(stmt)
    session_record = result.scalar_one_or_none()

    if not session_record:
        raise credentials_exception
        
    now_utc = datetime.now(timezone.utc)
    if session_record.expires_at.replace(tzinfo=timezone.utc) < now_utc:
        # Удаляем просроченную сессию
        await db.execute(UserSession.__table__.delete().where(UserSession.id == session_record.id))
        await db.commit()
        raise credentials_exception

    # Получаем пользователя по ID, привязанному к сессии
    user = await get_user_by_id(db, user_id=session_record.user_id)
    
    if user is None or not user.is_active:
        raise credentials_exception
    
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Зависимость для эндпоинтов, доступных только администратору"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав. Требуется роль администратора.")
    return current_user