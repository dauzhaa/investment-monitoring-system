from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, String, UniqueConstraint, DateTime, Text
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from enum import Enum
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User

class ReportStatus(str, Enum):
    OVERDUE = "Просрочен"
    SUBMITTED = "Сдан"
    NOT_PLANNED = "Не запланировано"

class InvestmentReport(Base):
    __tablename__ = 'investment_reports'

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    forecast_annual: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q1: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q2: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q3: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q4: Mapped[float] = mapped_column(Float, default=0.0)
    fact_annual: Mapped[float] = mapped_column(Float, default=0.0)
    
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(
        String(50), 
        default=ReportStatus.OVERDUE.value,  # По умолчанию "Просрочен"
        nullable=False
    )
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by_user: Mapped["User"] = relationship(back_populates="reports")

    organization: Mapped["Organization"] = relationship(back_populates="reports")

    __table_args__ = (UniqueConstraint('organization_id', 'year', name='_org_year_uc'),)