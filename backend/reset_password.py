import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models import User
from passlib.context import CryptContext

# Настройка хэширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_admin_password():
    email = "admin@obr72.ru"
    new_password = "admin"
    
    print(f"🔍 Ищу пользователя {email}...")
    
    async with AsyncSessionLocal() as session:
        # Ищем админа
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        hashed_pw = pwd_context.hash(new_password)
        
        if user:
            print(f"✅ Пользователь найден! Сбрасываю пароль на '{new_password}'...")
            user.hashed_password = hashed_pw
            user.is_active = True
            user.is_superuser = True
            session.add(user)
        else:
            print(f"⚠️ Пользователь не найден. Создаю нового...")
            new_user = User(
                email=email,
                hashed_password=hashed_pw,
                is_active=True,
                is_superuser=True
            )
            session.add(new_user)
            
        await session.commit()
        print("🚀 Готово! Теперь можно входить.")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())