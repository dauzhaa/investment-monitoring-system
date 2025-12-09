from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Any, Literal

class ReportBase(BaseModel):
    report_year: int
    
class ReportCreate(ReportBase):
    data: dict[str, Any] | None = None
    
class Report(ReportBase):
    id: int
    organization_id: int
    status: Literal["Просрочен", "Сдан", "Не запланировано"] 
    forecast_annual: float
    fact_annual: float
    comment: str | None = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class ReportUpdate(BaseModel):
    status: Literal["Просрочен", "Сдан"]