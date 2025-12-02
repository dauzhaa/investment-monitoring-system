# backend/app/models/municipality.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .dictionaries import District  # ← ВОТ ТАК!

class Municipality(Base):
    __tablename__ = 'municipalities'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_districts.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Связи
    district: Mapped["District"] = relationship()  # ← District!
    organizations: Mapped[list["Organization"]] = relationship(back_populates="municipality_ref")