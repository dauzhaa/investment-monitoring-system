from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class Organization(Base):
    """Сущность: Организация"""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    inn = Column(String, unique=True, index=True, nullable=False)
    
    # Внешние ключи на справочники
    district_id = Column(Integer, ForeignKey("directory_districts.id"), nullable=True)
    okved_id = Column(Integer, ForeignKey("directory_okveds.id"), nullable=True)
    
    # Атрибуты
    is_smp = Column(Boolean, default=False) # Субъект малого предпринимательства
    email = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    district = relationship("District", back_populates="organizations")
    okved = relationship("Okved", back_populates="organizations")
    reports = relationship("InvestmentReport", back_populates="organization")