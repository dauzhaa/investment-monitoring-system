# backend/app/models/user.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey
from typing import List, TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .investment_report import InvestmentReport

class User(Base):
    __tablename__ = 'user'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связь 1:N -> User принадлежит одной Organization
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization.id"), nullable=True, index=True
    )
    
    # Relationship
    organization: Mapped["Organization"] = relationship(back_populates='users')
    
    reports: Mapped[List["InvestmentReport"]] = relationship(
        back_populates="created_by_user"
    )