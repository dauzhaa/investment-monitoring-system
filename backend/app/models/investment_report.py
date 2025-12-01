from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint, String
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization

class InvestmentReport(Base):
    __tablename__ = 'investment_reports'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ИСПРАВЛЕНО: ссылаемся на 'organizations.id'
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    forecast_annual: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q1: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q2: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q3: Mapped[float] = mapped_column(Float, default=0.0)
    fact_q4: Mapped[float] = mapped_column(Float, default=0.0)
    fact_annual: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[str] = mapped_column(String(50), default="Не сдан")

    organization: Mapped["Organization"] = relationship(back_populates="reports")

    __table_args__ = (UniqueConstraint('organization_id', 'year', name='_org_year_uc'),)