from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization

class User(Base):
    __tablename__ = 'users'  # <--- Множественное число
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Связь с Organization (1:N)
    # ИСПРАВЛЕНО: ссылаемся на 'organizations.id'
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id"), nullable=True, index=True
    )
    
    organization: Mapped["Organization"] = relationship(back_populates='users')