from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
# Если у тебя есть get_current_user, раскомментируй и используй его:
# from app.api.dependencies import get_current_user 
from app.services.gigachat_service import gigachat
from app.services.bot_analytics import BotAnalyticsService
from app.services.bot_tools import TOOLS, SYSTEM_PROMPT

router = APIRouter()

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., max_length=20)

@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    analytics = BotAnalyticsService(db)
    
    # Формируем историю сообщений
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    full_messages.extend([m.model_dump() for m in request.messages])
    
    try:
        result = await gigachat.chat_with_tools(full_messages, TOOLS, analytics)
        return {"answer": result["text"]}
    except Exception as e:
        print(f"Ошибка бота: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обращении к ИИ")