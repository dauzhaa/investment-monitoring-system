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
        
        # БЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ ТОКЕНОВ (GigaChat может отдавать usage=null)
        if data.get("usage"):
            total_tokens += data["usage"].get("total_tokens", 0)
            
        message = data["choices"][0]["message"]
        messages.append(message)
        
        # Шаг 2: Если нейросеть решила вызвать функцию
        if message.get("tool_calls"):
            executed_tools = []
            
            for tool_call in message["tool_calls"]:
                # Безопасно парсим название и аргументы
                func_obj = tool_call.get("function", {})
                func_name = func_obj.get("name")
                raw_args = func_obj.get("arguments", "{}")
                
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}
                
                # Вызываем нашу функцию из БД
                func = getattr(analytics_service, func_name, None)
                if func:
                    try:
                        result = await func(**args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": "Функция не найдена"}
                
                # Сохраняем для фронтенда
                executed_tools.append({
                    "name": func_name,
                    "arguments": args,
                    "result": result
                })
                
                # Возвращаем результат обратно нейросети
                messages.append({
                    "role": "tool", # Указываем, что это ответ от инструмента
                    "tool_call_id": tool_call.get("id", ""),
                    "content": json.dumps(result, ensure_ascii=False)
                })
                
            # Шаг 3: Просим нейросеть сделать финальный вывод
            final_response = await self._client.post(
                self.API_URL,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "model": settings.GIGACHAT_MODEL,
                    "messages": messages,
                    "temperature": 0.2
                }
            )
            
            # ВАЖНО: Ловим ошибки, если GigaChat отклонил наш JSON на Шаге 3
            if not final_response.is_success:
                print(f"Ошибка GigaChat (Шаг 3): {final_response.text}")
            final_response.raise_for_status()
            
            final_data = final_response.json()
            if final_data.get("usage"):
                total_tokens += final_data["usage"].get("total_tokens", 0)
                
            return {
                "text": final_data["choices"][0]["message"]["content"], 
                "tokens": total_tokens,
                "tool_calls": executed_tools # Прокидываем наружу!
            }
            
        # Если вызов функции не потребовался (обычный ответ)
        return {"text": message.get("content", ""), "tokens": total_tokens}

gigachat = GigaChatService()