"""
Main FastAPI Application — SaaS Educativo White-Label
"""

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import create_tables


# ===========================================
# Lifespan (startup/shutdown)
# ===========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Startup
    print(f"🚀 Iniciando {settings.APP_NAME}...")
    await create_tables()
    print("✅ Base de datos lista")
    
    yield
    
    # Shutdown
    print("👋 Cerrando aplicación...")


# ===========================================
# FastAPI App
# ===========================================
app = FastAPI(
    title=settings.APP_NAME,
    description="SaaS Educativo White-Label con IA",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ===========================================
# CORS Middleware
# ===========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Exception Handlers
# ===========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Maneja todas las excepciones no controladas."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# ===========================================
# Health Check
# ===========================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de salud para verificar que el servicio está activo."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs" if settings.DEBUG else "Desactivado en producción",
        "version": "1.0.0"
    }


# ===========================================
# Routers (se importan después de definir app)
# ===========================================
# Sprint 2: Auth
from app.api.v1.auth import router as auth_router
app.include_router(
    auth_router,
    prefix=settings.API_V1_PREFIX,
    tags=["Autenticación"]
)

# Los routers restantes se registrarán en sprints posteriores
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.analytics import router as analytics_router

app.include_router(documents_router, prefix=settings.API_V1_PREFIX, tags=["Documentos"])
app.include_router(chat_router, prefix=settings.API_V1_PREFIX, tags=["Chat RAG"])
app.include_router(evaluations_router, prefix=settings.API_V1_PREFIX, tags=["Evaluaciones"])
app.include_router(analytics_router, prefix=settings.API_V1_PREFIX, tags=["Analíticas"])


# ===========================================
# Debug: List routes
# ===========================================
if settings.DEBUG:
    @app.on_event("startup")
    async def list_routes():
        print("\n📋 Rutas registradas:")
        for route in app.routes:
            if hasattr(route, "path"):
                methods = getattr(route, "methods", {"GET"})
                print(f"  {list(methods)[0] if methods else 'GET':6} {route.path}")
        print()