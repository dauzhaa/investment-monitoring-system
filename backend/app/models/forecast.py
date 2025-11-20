# backend/app/models/forecast.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey, Date, JSON
from datetime import date
from app.models.base import Base

class Forecast(Base):
    __tablename__ = 'forecast'

    id: Mapped[int] = mapped_column(primary_key=True)
    
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"), index=True)
    
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_amount: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=False)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=False)
    
    meta_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="forecasts")