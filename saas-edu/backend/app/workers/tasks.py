"""
Tareas asíncronas de Celery.
Procesamiento de documentos, generación de quizzes, etc.
"""

import asyncio
from typing import Optional

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal


# ===========================================
# Helper to run async code in sync context
# ===========================================
def run_async(coro):
    """Ejecuta una coroutine en contexto síncrono."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create new loop for nested async
            return asyncio.run(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


# ===========================================
# Document Tasks
# ===========================================
@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_document_task",
    max_retries=3,
    soft_time_limit=600,  # 10 minutes
    time_limit=660  # 11 minutes hard limit
)
def process_document_task(
    self: Task,
    document_id: str,
    tenant_id: str
) -> dict:
    """
    Procesa un documento de forma asíncrona.
    
    Args:
        document_id: ID del documento
        tenant_id: ID del tenant
        
    Returns:
        Dict con resultado
    """
    print(f"📄 Iniciando procesamiento de documento: {document_id}")
    
    try:
        async def _process():
            from app.services.document_service import DocumentProcessor
            
            async with AsyncSessionLocal() as db:
                chunk_count, vector_ids = await DocumentProcessor.process_document(
                    document_id=document_id,
                    tenant_id=tenant_id,
                    db=db
                )
                await db.commit()
                return {"chunk_count": chunk_count, "vector_ids": len(vector_ids)}
        
        result = run_async(_process())
        print(f"✅ Documento procesado exitosamente: {document_id}")
        return result
        
    except SoftTimeLimitExceeded:
        print(f"⏱️ Time limit exceeded para documento: {document_id}")
        _mark_document_failed(document_id, "Time limit exceeded")
        raise
        
    except Exception as exc:
        print(f"❌ Error procesando documento {document_id}: {exc}")
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            countdown = 60 * (2 ** retry_count)  # 1min, 2min, 4min
            raise self.retry(exc=exc, countdown=countdown)
        else:
            _mark_document_failed(document_id, str(exc))
            raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.delete_document_task",
    max_retries=2,
    soft_time_limit=60
)
def delete_document_task(
    self: Task,
    document_id: str,
    tenant_id: str
) -> dict:
    """
    Elimina un documento de forma asíncrona.
    
    Args:
        document_id: ID del documento
        tenant_id: ID del tenant
        
    Returns:
        Dict con resultado
    """
    print(f"🗑️ Iniciando eliminación de documento: {document_id}")
    
    try:
        async def _delete():
            from app.services.document_service import DocumentService
            
            async with AsyncSessionLocal() as db:
                service = DocumentService(db)
                success = await service.delete_document(document_id, tenant_id)
                await db.commit()
                return {"success": success}
        
        result = run_async(_delete())
        print(f"✅ Documento eliminado exitosamente: {document_id}")
        return result
        
    except Exception as exc:
        print(f"❌ Error eliminando documento {document_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


# ===========================================
# Evaluation Tasks
# ===========================================
@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_evaluation_task",
    max_retries=3,
    soft_time_limit=300,  # 5 minutes
    time_limit=360
)
def generate_evaluation_task(
    self: Task,
    evaluation_id: str,
    tenant_id: str
) -> dict:
    """
    Genera preguntas para una evaluación de forma asíncrona.
    
    Args:
        evaluation_id: ID de la evaluación
        tenant_id: ID del tenant
        
    Returns:
        Dict con resultado
    """
    print(f"📝 Iniciando generación de evaluación: {evaluation_id}")
    
    try:
        async def _generate():
            from app.services.evaluation_service import EvaluationService
            
            async with AsyncSessionLocal() as db:
                service = EvaluationService(db)
                question_count = await service.generate_questions(
                    evaluation_id=evaluation_id,
                    tenant_id=tenant_id
                )
                await db.commit()
                return {"question_count": question_count}
        
        result = run_async(_generate())
        print(f"✅ Evaluación generada exitosamente: {evaluation_id}")
        return result
        
    except Exception as exc:
        print(f"❌ Error generando evaluación {evaluation_id}: {exc}")
        
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            countdown = 60 * (2 ** retry_count)
            raise self.retry(exc=exc, countdown=countdown)
        else:
            raise


@celery_app.task(
    bind=True,
    name="app.workers.tasks.grade_evaluation_task",
    max_retries=2,
    soft_time_limit=120
)
def grade_evaluation_task(
    self: Task,
    attempt_id: str,
    tenant_id: str
) -> dict:
    """
    Califica las respuestas de un intento de evaluación.
    
    Args:
        attempt_id: ID del intento
        tenant_id: ID del tenant
        
    Returns:
        Dict con resultado
    """
    print(f"📊 Iniciando calificación de intento: {attempt_id}")
    
    try:
        async def _grade():
            from app.services.evaluation_service import EvaluationService
            
            async with AsyncSessionLocal() as db:
                service = EvaluationService(db)
                result = await service.grade_attempt(
                    attempt_id=attempt_id,
                    tenant_id=tenant_id
                )
                await db.commit()
                return result
        
        result = run_async(_grade())
        print(f"✅ Intento calificado exitosamente: {attempt_id}")
        return result
        
    except Exception as exc:
        print(f"❌ Error calificando intento {attempt_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


# ===========================================
# Helper Functions
# ===========================================
def _mark_document_failed(document_id: str, error_message: str):
    """Marca un documento como fallido."""
    async def _mark():
        from app.models import Document, DocumentStatus
        
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if document:
                document.status = DocumentStatus.FAILED.value
                document.error_message = error_message
                await db.commit()
    
    try:
        run_async(_mark())
    except Exception as e:
        print(f"Error marcando documento como fallido: {e}")