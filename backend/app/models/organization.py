# backend/app/models/organization.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .directories import District, Okved, OrgCategory
    from .user import User
    from .investment_forecast import InvestmentForecast
    from .investment_fact import InvestmentFact
    from .report_submission import ReportSubmission
    from .uploaded_file import UploadedFile
    from .notification import Notification


class Organization(Base):
    """Организация — основная сущность системы (297 записей)."""
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    inn: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, index=True
    )
    okpo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_smp: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_email: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # FK на справочники
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_districts.id", ondelete="SET NULL"), nullable=True
    )
    okved_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_okveds.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_org_categories.id", ondelete="SET NULL"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Связи со справочниками
    district: Mapped["District"] = relationship(back_populates="organizations")
    okved: Mapped["Okved"] = relationship(back_populates="organizations")
    category: Mapped["OrgCategory"] = relationship(back_populates="organizations")

    # Связи с сущностями
    users: Mapped[List["User"]] = relationship(back_populates="organization")
    forecasts: Mapped[List["InvestmentForecast"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    facts: Mapped[List["InvestmentFact"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    submissions: Mapped[List["ReportSubmission"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    uploaded_files: Mapped[List["UploadedFile"]] = relationship(
        back_populates="organization"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="organization"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, inn='{self.inn}', name='{self.name[:50]}')>"