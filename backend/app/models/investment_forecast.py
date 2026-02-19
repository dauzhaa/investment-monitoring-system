# backend/app/models/investment_forecast.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class InvestmentForecast(Base):
    """
    Прогнозы инвестиций (годовые).
    
    Хранит ВСЮ историю: первоначальный прогноз + все уточнения.
    
    Пример для организации X, 2024 год:
      | forecast_type | revision_date | forecast_amount |
      |---------------|---------------|-----------------|
      | initial       | NULL          | 5 000           |
      | revised       | 2024-04-23    | 5 375           |
      | revised       | 2024-07-19    | 5 041           |
      | revised       | 2024-10-23    | 6 710           |
      | revised       | 2024-12-16    | 7 142           |
    """
    __tablename__ = "investment_forecasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_amount: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    forecast_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # 'initial' / 'revised'
    )
    revision_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="forecasts")
    created_by_user: Mapped["User"] = relationship(back_populates="created_forecasts")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "year", "forecast_type", "revision_date",
            name="_org_year_type_date_uc"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestmentForecast(org_id={self.organization_id}, "
            f"year={self.year}, type='{self.forecast_type}', "
            f"amount={self.forecast_amount})>"
        )