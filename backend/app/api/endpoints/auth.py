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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

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
        secure=False, 
        path="/" 
    )
    
    return {"message": "Успешный вход", "role": user.role}

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

# ==================== ВЕРИФИКАЦИЯ EMAIL ====================

def generate_numeric_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

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
    
    # Mock отправки email
    logger.info("\n" + "="*50)
    logger.info(f"📧 EMAIL MOCK: Код подтверждения для {current_user.email} -> {code}")
    logger.info("="*50 + "\n")
    
    return {"message": "Код подтверждения отправлен на почту"}

class VerifyCodeRequest(BaseModel):
    code: str

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