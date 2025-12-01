from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization

class District(Base):
    __tablename__ = "directory_districts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    # Связь с организациями
    organizations: Mapped[List["Organization"]] = relationship(back_populates="district")

class Okved(Base):
    __tablename__ = "directory_okveds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    # Связь с организациями
    organizations: Mapped[List["Organization"]] = relationship(back_populates="okved")