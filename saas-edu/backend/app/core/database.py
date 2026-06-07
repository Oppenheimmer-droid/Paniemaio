"""
Configuración de base de datos con SQLAlchemy 2.x async.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ===========================================
# Engine async
# ===========================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


# ===========================================
# Session factory
# ===========================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ===========================================
# Base class for models
# ===========================================
class Base(DeclarativeBase):
    """Base class para todos los modelos SQLAlchemy."""
    pass


# ===========================================
# Dependency: Get DB session
# ===========================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que provee una sesión de base de datos.
    Se usa en las rutas de FastAPI.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ===========================================
# Utility: Create all tables
# ===========================================
async def create_tables():
    """Crea todas las tablas en la base de datos."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ===========================================
# Utility: Drop all tables
# ===========================================
async def drop_tables():
    """Elimina todas las tablas de la base de datos."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)