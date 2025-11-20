# backend/app/models/user.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey
from typing import List
from app.models.base import Base

class User(Base):
    __tablename__ = 'user'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization.id"), nullable=True, index=True
    )
    
    organization: Mapped["Organization | None"] = relationship(back_populates='users')
    
    reports: Mapped[List["InvestmentReport"]] = relationship(
        back_populates="created_by_user"
    )