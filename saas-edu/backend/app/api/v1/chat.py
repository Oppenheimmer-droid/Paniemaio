"""
API Endpoints de Chat RAG.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, CurrentUser
from app.services.rag_service import RAGService
from app.schemas.schemas import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatMessageResponse,
    ErrorResponse,
)


router = APIRouter(prefix="/chat", tags=["Chat RAG"])


def get_rag_service(db: AsyncSession = Depends(get_db)) -> RAGService:
    """Dependency para RAGService."""
    return RAGService(db)


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear sesión de chat",
    description="Crea una nueva sesión de chat."
)
async def create_session(
    request: ChatSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Endpoint para crear sesión de chat."""
    session = await rag_service.create_session(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        title=request.title,
        document_id=request.document_id
    )
    
    return ChatSessionResponse.model_validate(session)


@router.get(
    "/sessions",
    summary="Listar sesiones",
    description="Lista las sesiones de chat del usuario."
)
async def list_sessions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Endpoint para listar sesiones."""
    sessions, total = await rag_service.list_sessions(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [ChatSessionResponse.model_validate(s) for s in sessions],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get(
    "/sessions/{session_id}/messages",
    summary="Obtener mensajes",
    description="Obtiene el historial de mensajes de una sesión."
)
async def get_messages(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Endpoint para obtener mensajes."""
    session = await rag_service.get_session(session_id, current_user.tenant_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": "Sesión no encontrada"}
        )
    
    # Verify ownership
    if session.user_id != current_user.id and current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_AUTHORIZED", "message": "No tienes acceso a esta sesión"}
        )
    
    messages = await rag_service.get_messages(session_id, current_user.tenant_id)
    
    return {
        "items": [ChatMessageResponse.model_validate(m) for m in messages],
        "total": len(messages)
    }


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    summary="Enviar pregunta",
    description="Procesa una pregunta y devuelve respuesta con citaciones."
)
async def query(
    request: ChatQueryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Endpoint para hacer preguntas RAG."""
    result = await rag_service.query(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question=request.question,
        session_id=request.session_id,
        document_id=request.document_id
    )
    
    return ChatQueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        session_id=result["session_id"] or "",
        tokens_used=result["tokens_used"],
        latency_ms=result["latency_ms"]
    )


@router.post(
    "/stream",
    summary="Enviar pregunta (streaming)",
    description="Procesa una pregunta con respuesta en streaming."
)
async def stream_query(
    request: ChatQueryRequest,
    current_user: CurrentUser = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Endpoint para streaming de chat."""
    
    async def generate():
        result = rag_service.stream_query(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            question=request.question,
            session_id=request.session_id
        )
        
        for chunk in result:
            yield f"data: {chunk}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )