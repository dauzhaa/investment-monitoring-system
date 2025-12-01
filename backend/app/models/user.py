from typing import List
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

class User(Base):
    __tablename__ = 'app_user' # Переименовали, чтобы не конфликтовать с системными
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True) # Может быть NULL, если вход по коду
    
    role: Mapped[str] = mapped_column(String(20), default='organization_user', nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Связь многие-ко-многим
    organizations: Mapped[List["UserOrganization"]] = relationship(back_populates="user")

class UserOrganization(Base):
    __tablename__ = 'user_organization'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('app_user.id', ondelete='CASCADE'))
    organization_id: Mapped[int] = mapped_column(ForeignKey('organization.id', ondelete='CASCADE'))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="organizations")
    organization: Mapped["Organization"] = relationship(back_populates="users")