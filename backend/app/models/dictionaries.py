from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class District(Base):
    """Справочник: Муниципальные районы"""
    __tablename__ = "directory_districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    organizations = relationship("Organization", back_populates="district")

class Okved(Base):
    """Справочник: Коды ОКВЭД"""
    __tablename__ = "directory_okveds"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True) # Расшифровка кода, если есть

    organizations = relationship("Organization", back_populates="okved")