from datetime import datetime
from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .base import Base

class Notification(Base):
    __tablename__ = 'notification'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('app_user.id', ondelete='CASCADE'))
    
    type: Mapped[str] = mapped_column(String(50)) # reminder, report_submitted
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())