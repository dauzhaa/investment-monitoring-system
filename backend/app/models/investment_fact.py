# backend/app/models/investment_fact.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class InvestmentFact(Base):
    """
    Фактические данные об инвестициях (квартальные и годовые).
    
    Квартальные (report_type='p2_quarterly'):
      quarter=1: январь-март
      quarter=2: январь-июнь
      quarter=3: январь-сентябрь
      quarter=4: январь-декабрь
      Суммы НАРАСТАЮЩИМ итогом (как в форме П-2).
    
    Годовая (report_type='p2_annual'):
      quarter=NULL — итог за год по форме П-2 (инвест) годовая.
    """
    __tablename__ = "investment_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    report_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'p2_quarterly' / 'p2_annual'
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    no_investment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="facts")
    created_by_user: Mapped["User"] = relationship(back_populates="created_facts")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "year", "quarter", "report_type",
            name="_org_year_quarter_type_uc"
        ),
        Index("ix_facts_org_year_quarter", "organization_id", "year", "quarter"),
    )

    def __repr__(self) -> str:
        q = f"Q{self.quarter}" if self.quarter else "annual"
        return (
            f"<InvestmentFact(org_id={self.organization_id}, "
            f"year={self.year}, {q}, amount={self.amount})>"
        )