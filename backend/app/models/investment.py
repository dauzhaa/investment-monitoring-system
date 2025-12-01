from typing import Optional
from datetime import datetime, date
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func, Numeric, Text, Date
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

# Таблица: Годовые планы (Сущность)
class InvestmentAnnual(Base):
    __tablename__ = 'investment_annual'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id', ondelete='CASCADE'))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    plan_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    forecast_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True)
    no_investment_reason: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey('app_user.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    organization: Mapped["Organization"] = relationship(back_populates="annual_plans")

# Таблица: Квартальные факты (Сущность)
class InvestmentQuarterly(Base):
    __tablename__ = 'investment_quarterly'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id', ondelete='CASCADE'))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    
    investment_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    
    report_submitted_date: Mapped[date] = mapped_column(Date, nullable=True)
    submission_status: Mapped[str] = mapped_column(String(50), default='not_submitted') 
    
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey('app_user.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    organization: Mapped["Organization"] = relationship(back_populates="quarterly_reports")