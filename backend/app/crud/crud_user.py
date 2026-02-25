from app.models.user import User
from app.models.user_credential import UserCredential
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Проверка email и пароля при входе (с учетом таблицы user_credentials)."""
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    
    # Ищем пароль в связанной таблице
    stmt = select(UserCredential).where(UserCredential.user_id == user.id)
    result = await db.execute(stmt)
    creds = result.scalar_one_or_none()
    
    if not creds:
        return None
        
    if not verify_password(password, creds.hashed_password):
        return None
        
    return user

async def create_user(db: AsyncSession, user_in: UserCreate) -> User | None:
    # 1. Создаем пользователя
    db_user = User(email=user_in.email, role="organization", is_active=True)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # 2. Создаем пароль в таблице credentials
    hashed_pw = hash_password(user_in.password)
    db_creds = UserCredential(user_id=db_user.id, hashed_password=hashed_pw)
    db.add(db_creds)
    await db.commit()
    
    return db_user