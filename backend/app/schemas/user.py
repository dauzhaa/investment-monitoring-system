from pydantic import BaseModel, EmailStr, ConfigDict, computed_field

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    is_active: bool
    organization_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_superuser(self) -> bool:
        return self.role == "admin"