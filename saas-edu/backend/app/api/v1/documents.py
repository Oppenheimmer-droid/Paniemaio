"""
API Endpoints de documentos.
Upload, list, status, delete.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, CurrentUser, require_teacher
from app.core.config import settings
from app.services.document_service import DocumentService
from app.schemas.schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    ErrorResponse,
)
from app.workers.tasks import process_document_task, delete_document_task


router = APIRouter(prefix="/documents", tags=["Documentos"])


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency para DocumentService."""
    return DocumentService(db)


# Allowed MIME types
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Documento encolado para procesamiento"},
        400: {"model": ErrorResponse, "description": "Archivo inválido"},
        413: {"model": ErrorResponse, "description": "Archivo demasiado grande"},
    },
    summary="Subir documento",
    description="Sube un documento y lo encola para procesamiento."
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    subject_id: Optional[str] = Form(None),
    topic_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    difficulty: int = Form(default=1, ge=1, le=5),
    current_user: CurrentUser = Depends(require_teacher),
    document_service: DocumentService = Depends(get_document_service)
):
    """Endpoint para subir documentos."""
    
    # Validar tipo MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": f"Tipo de archivo no soportado: {file.content_type}. "
                          f"Soporta: {', '.join(ALLOWED_MIME_TYPES.keys())}"
            }
        )
    
    # Leer contenido
    content = await file.read()
    file_size = len(content)
    
    # Validar tamaño
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"El archivo excede el límite de {settings.MAX_FILE_SIZE_MB}MB"
            }
        )
    
    # Guardar archivo
    file_path = await document_service.save_file(
        file_content=content,
        filename=file.filename,
        tenant_id=current_user.tenant_id
    )
    
    # Crear registro de documento
    document = await document_service.create_document(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        title=title,
        subject_id=subject_id,
        topic_id=topic_id,
        description=description,
        difficulty=difficulty
    )
    
    # Encolar tarea de procesamiento
    process_document_task.delay(
        document_id=document.id,
        tenant_id=current_user.tenant_id
    )
    
    return {
        "id": document.id,
        "title": document.title,
        "status": document.status,
        "message": "Documento encolado para procesamiento"
    }


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="Listar documentos",
    description="Lista los documentos del tenant con paginación."
)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Endpoint para listar documentos."""
    
    documents, total = await document_service.list_documents(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        status=status_filter
    )
    
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Documento encontrado"},
        404: {"model": ErrorResponse, "description": "Documento no encontrado"},
    },
    summary="Obtener documento",
    description="Obtiene los detalles de un documento."
)
async def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Endpoint para obtener un documento."""
    
    document = await document_service.get_document(
        document_id=document_id,
        tenant_id=current_user.tenant_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Documento no encontrado"
            }
        )
    
    return DocumentResponse.model_validate(document)


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
    summary="Estado de procesamiento",
    description="Obtiene el estado actual del procesamiento de un documento."
)
async def get_document_status(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Endpoint para consultar estado de documento."""
    
    document = await document_service.get_document(
        document_id=document_id,
        tenant_id=current_user.tenant_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Documento no encontrado"
            }
        )
    
    return DocumentStatusResponse(
        id=document.id,
        status=document.status,
        chunk_count=document.chunk_count,
        error_message=document.error_message
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Documento eliminado"},
        404: {"model": ErrorResponse, "description": "Documento no encontrado"},
    },
    summary="Eliminar documento",
    description="Elimina un documento y sus vectores asociados."
)
async def delete_document(
    document_id: str,
    current_user: CurrentUser = Depends(require_teacher),
    document_service: DocumentService = Depends(get_document_service)
):
    """Endpoint para eliminar un documento."""
    
    document = await document_service.get_document(
        document_id=document_id,
        tenant_id=current_user.tenant_id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DOCUMENT_NOT_FOUND",
                "message": "Documento no encontrado"
            }
        )
    
    # Encolar tarea de eliminación
    delete_document_task.delay(
        document_id=document_id,
        tenant_id=current_user.tenant_id
    )
    
    return None