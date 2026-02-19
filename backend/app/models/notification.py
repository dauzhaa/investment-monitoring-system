# backend/app/models/notification.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User
    from .organization import Organization


class Notification(Base):
    """
    Уведомления и email-напоминания.
    
    Типы:
      - 'reminder': напоминание о сдаче отчёта
      - 'deadline_warning': предупреждение о приближающемся дедлайне
      - 'system': системное уведомление
    """
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    user: Mapped["User"] = relationship(back_populates="notifications")
    organization: Mapped["Organization"] = relationship(back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, type='{self.type}', "
            f"is_read={self.is_read})>"
        )