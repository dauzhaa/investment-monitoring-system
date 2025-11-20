from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Импорты
from app.api.routers import analytics
from app.core.config import settings
from app.api.endpoints import auth, reports
from app.api.routers import organizations
from app.api.routers import monitoring

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Investment Monitoring System...")
    yield
    logger.info("Shutting down Investment Monitoring System...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Система мониторинга инвестиций",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",], # Для разработки можно оставить *, перед деплоем верни список доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Auth Router
app.include_router(
    auth.router,
    prefix="/api/v1/auth",  # <--- Обрати внимание на этот путь
    tags=["1. Authentication"]
)

# 2. Reports Router
app.include_router(
    reports.router,
    prefix="/api/v1/reports",
    tags=["2. Reports"]
)

# 3. Analytics Router
app.include_router(
    analytics.router,
    prefix="/api/v1/analytics", # <--- Добавил префикс для порядка
    tags=["3. Analytics"]
)

app.include_router(
    monitoring.router, 
    prefix="/api/v1/monitoring", 
    tags=["5. Monitoring"]
)

app.include_router(
    organizations.router,
    prefix="/api/v1/organizations",
    tags=["4. Organizations"]
)

@app.get("/")
async def root():
    return {"status": "running", "version": settings.APP_VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}