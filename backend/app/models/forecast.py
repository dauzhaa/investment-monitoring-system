from sqlalchemy import Column, Integer, Float, ForeignKey, String, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Дата прогноза (месяц/год)
    date = Column(String, nullable=False) 
    # Сумма прогноза
    amount = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")