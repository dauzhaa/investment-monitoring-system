from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Импорты
from app.api.routers import analytics, districts, dictionaries
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
        "http://127.0.0.1:3000",
        "http://77.95.201.98",     
        "http://77.95.201.98:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Auth Router
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
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
    prefix="/api/v1/analytics",
    tags=["3. Analytics"]
)

# 4. Organizations Router
app.include_router(
    organizations.router,
    prefix="/api/v1/organizations",
    tags=["4. Organizations"]
)

# 5. Monitoring Router
app.include_router(
    monitoring.router, 
    prefix="/api/v1/monitoring", 
    tags=["5. Monitoring"]
)

# 6. Districts Router (новый)
app.include_router(
    districts.router,
    prefix="/api/v1/districts",
    tags=["6. Districts"]
)

app.include_router(
    dictionaries.router,
    prefix="/api/v1/dictionaries",
    tags=["6. Dictionaries"]
)

@app.get("/")
async def root():
    return {"status": "running", "version": settings.APP_VERSION}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}