from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User


class UserSession(Base):
    """
    Серверные сессии (замена JWT).
    
    Токен хранится в httpOnly cookie на клиенте.
    При каждом запросе — проверка токена в БД.
    
    Преимущества перед JWT:
      - Мгновенный отзыв (DELETE из таблицы)
      - Видны все активные сессии пользователя
      - Автоистечение по expires_at
    """
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связь
    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(user_id={self.user_id}, token='{self.session_token[:8]}...')>"