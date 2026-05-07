from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, ForeignKey, UniqueConstraint
from app.models.base import Base

class OrganizationIPO(Base):
    """Кэшированные годовые результаты ИПО для аналитики."""
    __tablename__ = "organization_ipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Итоговый балл
    ipo_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Компоненты ИПО
    d_score: Mapped[float] = mapped_column(Float, nullable=False) # Дисциплина (rho)
    a_score: Mapped[float] = mapped_column(Float, nullable=False) # Качество (alpha)
    e_score: Mapped[float | None] = mapped_column(Float, nullable=True) # Исполнение (beta)

    # Связь с организацией
    organization = relationship("Organization")

    __table_args__ = (
        UniqueConstraint("organization_id", "year", name="uq_org_ipo_year"),
    )