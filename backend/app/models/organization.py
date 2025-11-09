from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from typing import List
from app.models.base import Base

class Organization(Base):
    __tablename__ = 'organization'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    inn: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    users: Mapped[List["User"]] = relationship(back_populates = 'organization')
    
    reports: Mapped[List["InvestmentReport"]] = relationship(
        back_populates="organization"
    )