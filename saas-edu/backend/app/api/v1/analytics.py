"""
API Endpoints de Analíticas.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_teacher, CurrentUser
from app.services.analytics_service import AnalyticsService
from app.schemas.schemas import (
    AnalyticsOverviewResponse,
    StudentProgressListResponse,
    DocumentUsageListResponse,
    ErrorResponse,
)


router = APIRouter(prefix="/analytics", tags=["Analíticas"])


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Overview",
    description="Obtiene resumen de analíticas para el dashboard."
)
async def get_overview(
    current_user: CurrentUser = Depends(require_teacher),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Endpoint para overview de analíticas."""
    data = await analytics_service.get_overview(current_user.tenant_id)
    return AnalyticsOverviewResponse(**data)


@router.get(
    "/students",
    summary="Progreso de estudiantes",
    description="Lista el progreso de todos los estudiantes."
)
async def get_students_progress(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_teacher),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Endpoint para progreso de estudiantes."""
    students, total = await analytics_service.get_students_progress(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size
    )
    
    return StudentProgressListResponse(
        items=students,
        total=total
    )


@router.get(
    "/documents",
    summary="Uso de documentos",
    description="Lista el uso de todos los documentos."
)
async def get_documents_usage(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_teacher),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Endpoint para uso de documentos."""
    documents, total = await analytics_service.get_documents_usage(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size
    )
    
    return DocumentUsageListResponse(
        items=documents,
        total=total
    )


@router.get(
    "/me",
    summary="Mis estadísticas",
    description="Obtiene las estadísticas del usuario actual (student)."
)
async def get_my_stats(
    current_user: CurrentUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Endpoint para estadísticas personales."""
    stats = await analytics_service.get_user_stats(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id
    )
    
    return stats