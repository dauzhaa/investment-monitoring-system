# backend/app/models/report_submission.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Date, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
from app.models.base import Base

if TYPE_CHECKING:
    from .organization import Organization


class ReportSubmission(Base):
    """
    Мониторинг сдачи отчётности.
    
    Статусы:
      - 'pending': дедлайн не наступил, отчёт не сдан
      - 'submitted': отчёт загружен
      - 'overdue': дедлайн прошёл, отчёт не сдан
    
    Дедлайн = конец квартала + 2 недели.
    days_overdue = MAX(0, today - deadline_date) для overdue.
    
    Celery-задача ежедневно обновляет статусы и отправляет напоминания.
    """
    __tablename__ = "report_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline_date: Mapped[Date] = mapped_column(Date, nullable=False)
    submitted_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    days_overdue: Mapped[int] = mapped_column(Integer, default=0)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reminder_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Связи
    organization: Mapped["Organization"] = relationship(back_populates="submissions")

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "year", "quarter",
            name="_org_year_quarter_submission_uc"
        ),
        Index("ix_submissions_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReportSubmission(org_id={self.organization_id}, "
            f"{self.year}-Q{self.quarter}, status='{self.status}')>"
        )