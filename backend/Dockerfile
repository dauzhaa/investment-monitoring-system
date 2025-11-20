# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей (нужны для сборки некоторых python-пакетов)
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]