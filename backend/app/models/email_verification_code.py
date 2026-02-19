# backend/app/models/email_verification_code.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User


class EmailVerificationCode(Base):
    """
    Коды верификации при входе.
    
    Процесс:
      1. Пользователь вводит email + пароль
      2. Пароль верифицирован → генерируется 6-значный код
      3. Код отправляется на email
      4. Пользователь вводит код → проверка (не истёк, не использован)
      5. Успех → создаётся сессия, код помечается is_used=True
    
    Код живёт 15 минут, одноразовый.
    """
    __tablename__ = "email_verification_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связь
    user: Mapped["User"] = relationship(back_populates="verification_codes")

    def __repr__(self) -> str:
        return f"<EmailVerificationCode(user_id={self.user_id}, is_used={self.is_used})>"