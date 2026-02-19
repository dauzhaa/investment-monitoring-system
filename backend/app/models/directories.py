# backend/app/models/directories.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization


class District(Base):
    """Справочник: Районы и города Тюменской области (27 записей)."""
    __tablename__ = "directory_districts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)

    # Связи
    organizations: Mapped[List["Organization"]] = relationship(back_populates="district")

    def __repr__(self) -> str:
        return f"<District(id={self.id}, name='{self.name}')>"


class Okved(Base):
    """Справочник: Коды ОКВЭД."""
    __tablename__ = "directory_okveds"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Связи
    organizations: Mapped[List["Organization"]] = relationship(back_populates="okved")

    def __repr__(self) -> str:
        return f"<Okved(id={self.id}, code='{self.code}')>"


class OrgCategory(Base):
    """Справочник: Категории организаций (1=МО, 2=Подвед., 3=ВУЗы, 4=Иные)."""
    __tablename__ = "directory_org_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Связи
    organizations: Mapped[List["Organization"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<OrgCategory(id={self.id}, code={self.code}, name='{self.name}')>"