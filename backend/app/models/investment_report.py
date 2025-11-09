from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, JSON, Enum as SQLEnum
from typing import List, Any
from app.models.base import Base
from enum import Enum

class ReportStatus(str, Enum):
    PENDING =  "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class InvestmentReport(Base):
    __tablename__ = "investment_report"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    report_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False),
        default = ReportStatus.PENDING,
        nullable = False
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization.id"), index=True
    )
    
    organization: Mapped["Organization"] = relationship(
        back_populates="reports"
    )
    
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id"), nullable=True, index=True
    )
    
    created_by_user: Mapped["User | None"] = relationship(
        back_populates="reports"
    )