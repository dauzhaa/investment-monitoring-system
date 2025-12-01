from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class InvestmentReport(Base):
    """Сущность: Инвестиционный отчет за год"""
    __tablename__ = "investment_reports"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    year = Column(Integer, nullable=False)
    
    # Данные (План и Факт по кварталам)
    forecast_annual = Column(Float, default=0.0) # Прогноз на год
    fact_q1 = Column(Float, default=0.0)
    fact_q2 = Column(Float, default=0.0)
    fact_q3 = Column(Float, default=0.0)
    fact_q4 = Column(Float, default=0.0)
    fact_annual = Column(Float, default=0.0)
    
    # Статусы сдачи (Сдан/Не сдан/Просрочен)
    status = Column(String, default="Не сдан") 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="reports")

    __table_args__ = (UniqueConstraint('organization_id', 'year', name='_org_year_uc'),)