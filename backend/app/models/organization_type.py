# backend/app/models/organization_type.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization

class OrganizationType(Base):
    __tablename__ = 'organization_types'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # "OOO", "PAO", "IP"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # "ООО", "ПАО", "ИП"
    
    organizations: Mapped[list["Organization"]] = relationship(back_populates="org_type_ref")