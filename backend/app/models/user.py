# backend/app/models/user.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user_credential import UserCredential
    from .email_verification_code import EmailVerificationCode
    from .user_session import UserSession
    from .uploaded_file import UploadedFile
    from .investment_forecast import InvestmentForecast
    from .investment_fact import InvestmentFact
    from .audit_log import AuditLog
    from .notification import Notification


class User(Base):
    """
    Пользователь системы.
    
    Роли:
      - 'admin': сотрудник департамента (organization_id = NULL)
      - 'organization': представитель организации (привязан к organization_id)
    
    Регистрации нет — аккаунты создаёт только admin.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'admin' / 'organization'
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="users")
    credential: Mapped["UserCredential"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    verification_codes: Mapped[List["EmailVerificationCode"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    uploaded_files: Mapped[List["UploadedFile"]] = relationship(
        back_populates="uploaded_by_user"
    )
    created_forecasts: Mapped[List["InvestmentForecast"]] = relationship(
        back_populates="created_by_user"
    )
    created_facts: Mapped[List["InvestmentFact"]] = relationship(
        back_populates="created_by_user"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        back_populates="user"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"