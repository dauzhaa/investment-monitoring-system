import httpx
import uuid
import time
import json
from app.core.config import settings

class GigaChatService:
    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def __init__(self):
        self._access_token: str | None = None
        self._expires_at: float = 0
        self._client = httpx.AsyncClient(
            verify=False,
            timeout=httpx.Timeout(30.0)
        )

    async def _get_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token
        
        response = await self._client.post(
            self.AUTH_URL,
            headers={
                "Authorization": f"Basic {settings.GIGACHAT_AUTH_KEY}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"scope": settings.GIGACHAT_SCOPE},
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._expires_at = data["expires_at"] / 1000
        return self._access_token

    async def chat_with_tools(self, messages: list[dict], tools: list[dict], analytics_service) -> dict:
        token = await self._get_token()
        total_tokens = 0
        
        # Шаг 1: Запрос к нейросети
        response = await self._client.post(
            self.API_URL,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "model": settings.GIGACHAT_MODEL,
                "messages": messages,
                "tools": tools,
                "temperature": 0.2
            }
        )
        response.raise_for_status()
        data = response.json()
        total_tokens += data["usage"]["total_tokens"]
        message = data["choices"][0]["message"]
        messages.append(message)
        
# Шаг 2: Если нейросеть решила вызвать функцию
        if message.get("tool_calls"):
            executed_tools = [] # <-- ДОБАВЛЯЕМ МАССИВ ДЛЯ ФРОНТА
            
            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                
                # Вызываем нашу функцию из БД
                func = getattr(analytics_service, func_name, None)
                if func:
                    try:
                        result = await func(**args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": "Функция не найдена"}
                
                # Сохраняем для отправки на фронт
                executed_tools.append({
                    "name": func_name,
                    "arguments": args,
                    "result": result
                })
                
                # Возвращаем результат обратно нейросети
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result, ensure_ascii=False)
                })
                
            # Шаг 3: Финальный вывод
            final_response = await self._client.post(...)
            final_data = final_response.json()
            total_tokens += final_data["usage"]["total_tokens"]
            
            # ВОЗВРАЩАЕМ ВМЕСТЕ С TOOL_CALLS
            return {
                "text": final_data["choices"][0]["message"]["content"], 
                "tokens": total_tokens,
                "tool_calls": executed_tools 
            }

gigachat = GigaChatService()