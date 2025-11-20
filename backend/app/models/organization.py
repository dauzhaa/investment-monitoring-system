# backend/app/models/organization.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, JSON
from typing import List
from app.models.base import Base
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .investment_report import InvestmentReport
    from .forecast import Forecast
class Organization(Base):
    __tablename__ = 'organization'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Новые поля
    municipality: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    org_type: Mapped[str] = mapped_column(String(50), nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cluster_group: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Обрати внимание: User здесь в кавычках, чтобы не было кругового импорта
    users: Mapped[List["User"]] = relationship(back_populates='organization')
    
    reports: Mapped[List["InvestmentReport"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    forecasts: Mapped[List["Forecast"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )