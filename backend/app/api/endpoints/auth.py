from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.crud_user import get_user_by_email, create_user, authenticate_user
from app.schemas.user import UserCreate, User as UserSchema
from app.models.user import User as DBUser
from app.core.security import create_access_token
from app.api.dependencies import get_current_user

router = APIRouter()

# Указываем response_model=UserSchema, чтобы FastAPI корректно собрал JSON
@router.post("/register", response_model=UserSchema)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=user_in.email)
    
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email уже зарегистрирован")
    
    new_user = await create_user(db, user_in=user_in)
    return new_user
        
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

# Здесь тоже указываем Pydantic-схему для возврата профиля на фронтенд
@router.post("/login/test-token", response_model=UserSchema)
async def test_token(current_user: DBUser = Depends(get_current_user)):
    return current_user