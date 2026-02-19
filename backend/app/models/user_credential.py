# backend/app/models/user_credential.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User


class UserCredential(Base):
    """
    Хранение пароля отдельно от профиля пользователя.
    
    Связь 1:1 с users.
    Пароль никогда не попадает в обычные SELECT по users.
    При проверке — отдельный запрос только когда нужно.
    """
    __tablename__ = "user_credentials"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связь
    user: Mapped["User"] = relationship(back_populates="credential")

    def __repr__(self) -> str:
        return f"<UserCredential(user_id={self.user_id})>"