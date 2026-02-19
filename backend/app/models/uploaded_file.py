# backend/app/models/uploaded_file.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization
    from .user import User


class UploadedFile(Base):
    """
    Метаданные загруженных файлов.
    
    Файлы хранятся на диске, путь = settings.UPLOAD_DIR / stored_filename.
    stored_filename — UUID-имя (напр. "a1b2c3d4-5678-9abc.xlsx").
    Пользователь никогда не видит реальный путь.
    
    Для PDF: has_signature / has_stamp заполняются ИИ-моделью.
    """
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'xlsx' / 'pdf'
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(20), default="pending"  # 'pending'/'processing'/'success'/'error'
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_signature: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_stamp: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="uploaded_files")
    uploaded_by_user: Mapped["User"] = relationship(back_populates="uploaded_files")

    def __repr__(self) -> str:
        return (
            f"<UploadedFile(id={self.id}, "
            f"filename='{self.original_filename}', "
            f"status='{self.processing_status}')>"
        )