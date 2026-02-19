# backend/app/models/audit_log.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from typing import Any, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User


class AuditLog(Base):
    """
    Журнал всех действий в системе.
    
    Логируется ВСЁ:
      - login, logout, login_failed
      - upload_file, delete_file
      - create_user, update_user, delete_user
      - send_reminder
      - update_forecast, create_fact
      - create_organization, update_organization
      - export_report
      - verify_email, change_password
    
    details (JSONB) — произвольные данные:
      {"old_status": "pending", "new_status": "submitted"}
      {"filename": "report.xlsx", "file_size": 45000}
      {"target_email": "org@mail.ru"}
    """
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связь
    user: Mapped["User"] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_log_created_at", "created_at"),
        Index("ix_audit_log_action", "action"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}')>"
        )