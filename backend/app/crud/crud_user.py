from fastapi import FastAPI
from app.models.user import User
from app.core.security import hash_password
from app.schemas import UserCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    query = select(User).where(User.email == email)
    
    result = await db.execute(query)
    
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User | None:
    hashed_password = hash_password(user_in.password)
    
    db_user = User(email=user_in.email, hashed_password = hashed_password, is_active=True)
    
    db.add(db_user)
    
    await db.commit()

    await db.refresh(db_user)
    
    return db_user
    
async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    query = select(User).where(User.id == user_id)
    
    result = await db.execute(query)
    
    return result.scalar_one_or_none()
    
    