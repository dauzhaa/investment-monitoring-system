# app/models/investment_report.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, JSON, Enum as SQLEnum, func, Float
from typing import List, Any
from app.models.base import Base
from datetime import datetime
from enum import Enum

class ReportStatus(str, Enum):
    PENDING =  "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class InvestmentReport(Base):
    __tablename__ = "investment_report"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Период
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False) # 1, 2, 3, 4
    
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False),
        default=ReportStatus.PENDING,
        nullable=False
    )

    # --- ФИНАНСОВЫЕ ПОКАЗАТЕЛИ (Вынесены из JSON для быстрого поиска) ---
    
    # Общая сумма инвестиций за этот квартал
    total_investment: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Источники финансирования (для диаграмм)
    budget_federal: Mapped[float] = mapped_column(Float, default=0.0)
    budget_regional: Mapped[float] = mapped_column(Float, default=0.0)
    own_funds: Mapped[float] = mapped_column(Float, default=0.0)

    # Весь сырой JSON отчета (на всякий случай)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False
    )
    
    # Связи
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organization.id"), index=True
    )
    organization: Mapped["Organization"] = relationship(back_populates="reports")
    
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"), nullable=True
    )
    created_by_user: Mapped["User | None"] = relationship(back_populates="reports")