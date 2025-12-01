from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization

class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # ИСПРАВЛЕНО: ссылаемся на 'organizations.id'
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    
    date: Mapped[str] = mapped_column(String, nullable=False) 
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="forecasts")