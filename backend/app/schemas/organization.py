from pydantic import BaseModel, EmailStr, ConfigDict

class OrganizationBase(BaseModel):
    name: str
    inn: str
    contact_email: str | None = None
    
class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)