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
    # Добавляем "Не запланировано" в список допустимых значений
    status: Literal["Просрочен", "Сдан", "Не запланировано"] 
    forecast_annual: float # Добавил для отображения
    fact_annual: float     # Добавил для отображения
    comment: str | None = None # Добавил комментарий
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class ReportUpdate(BaseModel):
    status: Literal["Просрочен", "Сдан"]