from pydantic import BaseModel, ConfigDict
from typing import Optional

class OrganizationBase(BaseModel):
    name: str
    inn: str
    is_smp: bool = False
    contact_email: Optional[str] = None
    district_id: Optional[int] = None
    okved_id: Optional[int] = None
    
class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    is_smp: Optional[bool] = None
    contact_email: Optional[str] = None
    district_id: Optional[int] = None
    okved_id: Optional[int] = None

class Organization(OrganizationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)