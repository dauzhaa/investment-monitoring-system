from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, JSON, ForeignKey, Boolean
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User
    from .investment_report import InvestmentReport
    from .forecast import Forecast
    from .dictionaries import District, Okved

class Organization(Base):
    __tablename__ = 'organizations' # Множественное число!
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Внешние ключи
    district_id: Mapped[int | None] = mapped_column(ForeignKey("directory_districts.id"), nullable=True)
    okved_id: Mapped[int | None] = mapped_column(ForeignKey("directory_okveds.id"), nullable=True)
    
    is_smp: Mapped[bool] = mapped_column(Boolean, default=False)
    municipality: Mapped[str | None] = mapped_column(String(255), nullable=True)
    org_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cluster_group: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Связи
    district: Mapped["District"] = relationship(back_populates="organizations")
    okved: Mapped["Okved"] = relationship(back_populates="organizations")
    users: Mapped[List["User"]] = relationship(back_populates='organization')
    
    reports: Mapped[List["InvestmentReport"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    
    forecasts: Mapped[List["Forecast"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )