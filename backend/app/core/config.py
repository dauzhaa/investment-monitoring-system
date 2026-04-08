"""
Configuration settings for the application
"""
from typing import List, Union, Optional
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Investment Monitoring System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    DATABASE_SYNC_URL: str = ""
    
    # Redis
    REDIS_URL: str
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON string for BACKEND_CORS_ORIGINS: {v}")
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v 
        raise ValueError(v)
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_PATH: str = "./uploads"
    
    # Email
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 465
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True   
    
    # --- ДОБАВЛЕННЫЕ ПОЛЯ ДЛЯ АДМИНА ---
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"
    
    # Объединяем конфигурацию в один блок
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore"
    )


# Создаем экземпляр настроек
settings = Settings()