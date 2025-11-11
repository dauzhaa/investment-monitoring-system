from pydantic import BaseModel, ConfigDict
from app.models.investment_report import ReportStatus
from datetime import datetime
from typing import Any
class ReportBase(BaseModel):
    report_year: int
    
class ReportCreate(ReportBase):
    data: dict[str, Any] | None = None
    
class Report(ReportBase):
    id: int
    organization_id: int
    status: ReportStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class ReportUpdate(BaseModel):
    status: ReportStatus