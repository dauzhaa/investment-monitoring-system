from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Any

class ExcelRowSchema(BaseModel):
    name: str = Field(..., min_length=2, description="Наименование организации")
    inn: str = Field(..., description="ИНН организации")
    is_smp: bool = Field(default=False)
    okpo: str | None = None
    okved_code: str | None = None
    forecast: float = Field(default=0.0)
    amount: float = Field(default=0.0)
    submit_date: date | None = None
    reason: str | None = None

    @field_validator("inn", mode="before")
    @classmethod
    def validate_inn(cls, v: Any) -> str:
        if not v:
            raise ValueError("ИНН не может быть пустым")
        cleaned = str(v).split('.')[0].strip()
        if not cleaned.isdigit() or len(cleaned) not in (10, 12):
            raise ValueError(f"ИНН должен состоять из 10 или 12 цифр, получено: '{cleaned}'")
        return cleaned

    @field_validator("is_smp", mode="before")
    @classmethod
    def parse_smp(cls, v: Any) -> bool:
        if not v: return False
        return str(v).strip().lower() == "да"

    @field_validator("forecast", "amount", mode="before")
    @classmethod
    def parse_floats(cls, v: Any) -> float:
        if v is None or str(v).strip() == "": 
            return 0.0
        if isinstance(v, (int, float)): 
            return float(v)
        try:
            cleaned = str(v).replace(" ", "").replace("\xa0", "").replace(",", ".")
            return float(cleaned)
        except ValueError:
            raise ValueError(f"Ожидается число, получено: '{v}'")

    @field_validator("submit_date", mode="before")
    @classmethod
    def parse_date_val(cls, v: Any) -> date | None:
        if not v: return None
        if isinstance(v, datetime): return v.date()
        if isinstance(v, date): return v
        if isinstance(v, str):
            try:
                return datetime.strptime(v.strip(), "%d.%m.%Y").date()
            except ValueError:
                raise ValueError(f"Неверный формат даты (ожидается ДД.ММ.ГГГГ), получено: '{v}'")
        raise ValueError("Неподдерживаемый формат даты")