from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User

class Notification(Base):
    __tablename__ = 'notifications'  # Множественное число

    id: Mapped[int] = mapped_column(primary_key=True)
    # ИСПРАВЛЕНО: ссылка на 'users.id', а не 'app_user.id'
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notifications")