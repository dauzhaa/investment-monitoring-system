from datetime import datetime, timedelta, timezone
import random
import string
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel

from app.core.database import get_db
from app.crud.crud_user import get_user_by_email, create_user, authenticate_user
from app.schemas.user import UserCreate, User as UserSchema
from app.models.user import User as DBUser
from app.models.user_session import UserSession
from app.models.email_verification_code import EmailVerificationCode
from app.core.security import generate_session_token
from app.api.dependencies import get_current_user

# ИМПОРТИРУЕМ НАШ БОЕВОЙ СЕРВИС ОТПРАВКИ
from app.services.notification_service import send_real_email

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== УТИЛИТЫ ====================

def generate_numeric_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

async def _create_user_session(user: DBUser, request: Request, response: Response, db: AsyncSession):
    """Вспомогательная функция для создания сессии и установки Cookie"""
    session_token = generate_session_token()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", None)
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    new_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=expires_at
    )
    db.add(new_session)
    user.last_login_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,
        secure=False, # В будущем для HTTPS в проде лучше ставить True
        path="/" 
    )
    
    return {"message": "Успешный вход", "role": user.role, "is_email_verified": user.is_email_verified}

# ==================== СХЕМЫ ЗАПРОСОВ ====================

class VerifyCodeRequest(BaseModel):
    code: str

class Login2FARequest(BaseModel):
    email: str
    password: str
    code: str

# ==================== РОУТЕРЫ ====================

@router.post("/register", response_model=UserSchema)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email уже зарегистрирован")
    
    new_user = await create_user(db, user_in=user_in)
    return new_user
        
@router.post("/login")
async def login(
    request: Request,
    response: Response, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный логин или пароль"
        )
    
    # 1. Если почта еще не подтверждена -> пускаем без 2FA (для доступа к профилю и верификации)
    if not user.is_email_verified:
        return await _create_user_session(user, request, response, db)
    
    # 2. Если почта подтверждена -> запускаем процесс 2FA (отправляем код)
    await db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user.id))
    
    code = generate_numeric_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15) # Код для входа живет 15 минут
    
    new_code = EmailVerificationCode(user_id=user.id, code=code, expires_at=expires_at)
    db.add(new_code)
    await db.commit()
    
    # ОТПРАВЛЯЕМ РЕАЛЬНОЕ ПИСЬМО
    subject = "Код для входа в ИнвестМонитор72"
    body = f"Здравствуйте!\n\nВаш проверочный код для входа в систему: {code}\n\nКод действителен 15 минут."
    await send_real_email(email_to=user.email, subject=subject, body=body)
    
    # Возвращаем статус 202, сообщая фронтенду, что требуется ввод кода
    return Response(
        status_code=status.HTTP_202_ACCEPTED, 
        content='{"require_2fa": true, "message": "Код отправлен на почту"}', 
        media_type="application/json"
    )

@router.post("/login/verify-2fa")
async def login_verify_2fa(
    payload: Login2FARequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Повторная проверка пароля для безопасности
    user = await authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Ошибка аутентификации")

    # Проверка введенного кода
    stmt = select(EmailVerificationCode).where(
        EmailVerificationCode.user_id == user.id,
        EmailVerificationCode.code == payload.code
    )
    db_code = (await db.execute(stmt)).scalar_one_or_none()

    if not db_code or db_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Неверный код или срок его действия истек")

    # Код верен, удаляем его и создаем сессию
    await db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user.id))
    await db.commit()
    
    return await _create_user_session(user, request, response, db)

@router.post("/logout")
async def logout(
    response: Response, 
    session_id: str | None = Cookie(default=None), 
    db: AsyncSession = Depends(get_db)
):
    if session_id:
        stmt = delete(UserSession).where(UserSession.session_token == session_id)
        await db.execute(stmt)
        await db.commit()
    
    response.delete_cookie(key="session_id", path="/")
    return {"message": "Вы успешно вышли из системы"}

@router.get("/me", response_model=UserSchema)
async def get_current_user_profile(current_user: DBUser = Depends(get_current_user)):
    return current_user

# ==================== ВЕРИФИКАЦИЯ EMAIL (ПРОФИЛЬ) ====================

@router.post("/request-verification")
async def request_email_verification(
    current_user: DBUser = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_email_verified:
        return {"message": "Email уже подтвержден"}

    await db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == current_user.id))
    
    code = generate_numeric_code()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    new_code = EmailVerificationCode(
        user_id=current_user.id,
        code=code,
        expires_at=expires_at
    )
    db.add(new_code)
    await db.commit()
    
    # ОТПРАВЛЯЕМ РЕАЛЬНОЕ ПИСЬМО
    subject = "Подтверждение Email - ИнвестМонитор72"
    body = f"Здравствуйте!\n\nВаш код для подтверждения электронной почты: {code}\n\nКод действителен 1 час."
    await send_real_email(email_to=current_user.email, subject=subject, body=body)
    
    return {"message": "Код подтверждения отправлен на почту"}

@router.post("/verify-email")
async def verify_email_code(
    payload: VerifyCodeRequest,
    current_user: DBUser = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    if current_user.is_email_verified:
        return {"message": "Email уже подтвержден"}

    stmt = select(EmailVerificationCode).where(
        EmailVerificationCode.user_id == current_user.id,
        EmailVerificationCode.code == payload.code
    )
    db_code = (await db.execute(stmt)).scalar_one_or_none()

    if not db_code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")
    
    if db_code.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Срок действия кода истек. Запросите новый.")

    current_user.is_email_verified = True
    await db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.user_id == current_user.id))
    await db.commit()

    return {"message": "Email успешно подтвержден"}