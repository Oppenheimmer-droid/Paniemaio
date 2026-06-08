# saas-edu/backend/app/main.py
"""Main FastAPI Application — SaaS Educativo White-Label"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import create_tables, AsyncSessionLocal

# ── Logging estructurado ─────────────────────────────────────────────────────
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        })

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Iniciando {settings.APP_NAME}...")
    try:
        await create_tables()
        print("✅ Base de datos lista")
    except Exception as e:
        print(f"⚠️  Error al crear tablas (puede que ya existan): {e}")
    yield
    print("👋 Cerrando aplicación...")


app = FastAPI(
    title=settings.APP_NAME,
    description="SaaS Educativo White-Label con IA",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handler ──────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/health/detailed", tags=["Health"])
async def health_detailed():
    """Health check detallado con estado de servicios."""
    checks = {"api": "ok", "database": "unknown", "redis": "unknown"}
    
    # Check DB
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL.replace('0', '6379') if ':6379/0' in settings.REDIS_URL else settings.REDIS_URL)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
    
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks, "version": "1.0.0"}

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs" if settings.DEBUG else "Desactivado en producción",
        "version": "1.0.0",
    }

# ── Routers ──────────────────────────────────────────────────────────────────
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.analytics import router as analytics_router

app.include_router(auth_router, prefix=settings.API_V1_PREFIX, tags=["Autenticación"])
app.include_router(documents_router, prefix=settings.API_V1_PREFIX, tags=["Documentos"])
app.include_router(chat_router, prefix=settings.API_V1_PREFIX, tags=["Chat RAG"])
app.include_router(evaluations_router, prefix=settings.API_V1_PREFIX, tags=["Evaluaciones"])
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX, tags=["Analíticas"])