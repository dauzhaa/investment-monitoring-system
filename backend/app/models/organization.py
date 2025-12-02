# backend/app/models/organization.py
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, ForeignKey, JSON
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .user import User
    from .investment_report import InvestmentReport
    from .directory_district import DirectoryDistrict
    from .directory_okved import DirectoryOkved
    from .organization_type import OrganizationType
    from .municipality import Municipality

class Organization(Base):
    __tablename__ = 'organizations'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    
    # Внешние ключи на справочники
    district_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_districts.id", ondelete="SET NULL")
    )
    okved_id: Mapped[int | None] = mapped_column(
        ForeignKey("directory_okveds.id", ondelete="SET NULL")
    )
    org_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_types.id", ondelete="SET NULL")
    )
    municipality_id: Mapped[int | None] = mapped_column(
        ForeignKey("municipalities.id", ondelete="SET NULL")
    )
    
    # Простые поля
    is_smp: Mapped[bool] = mapped_column(Boolean, default=False)
    # coordinates: JSON УДАЛИМ! (см. пункт 2)
    # cluster_group: УДАЛИМ! (см. пункт 3)
    
    # Связи (relationships)
    district: Mapped["DirectoryDistrict"] = relationship()
    okved: Mapped["DirectoryOkved"] = relationship()
    org_type_ref: Mapped["OrganizationType"] = relationship(back_populates="organizations")
    municipality_ref: Mapped["Municipality"] = relationship(back_populates="organizations")
    
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    reports: Mapped[list["InvestmentReport"]] = relationship(back_populates="organization")