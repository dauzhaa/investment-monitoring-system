from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import crud_user
from app.schemas import User, UserCreate
from app.core.security import verify_password, create_access_token


router = APIRouter()

@router.post("/register")
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    db_user = await crud_user.get_user_by_email(db, email=user_in.email)
    
    if db_user:
        raise HTTPException(status_code = 400, detail="email уже зарегистрирован")
    
    new_user = await crud_user.create_user(db, user_in=user_in)
    
    return new_user
        
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud_user.get_user_by_email(db, form_data.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="Неправильное имя пользователя или пароль")
    
    password = await verify_password(form_data.password, user.password)
    
    if not password:
        raise HTTPException(status_code=401, detail="Неправильное имя пользователя или пароль")
    
    token = await create_access_token(data={"sub": user.email})
    
    return {"access_token": token, "token_type": "bearer"}
    