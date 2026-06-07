"""
Configuración de Celery para tareas asíncronas.
"""

from celery import Celery

from app.core.config import settings


# ===========================================
# Celery App Configuration
# ===========================================
celery_app = Celery(
    "saas_edu",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
    ]
)

# ===========================================
# Celery Configuration
# ===========================================
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.workers.tasks.process_document_task": {"queue": "documents"},
        "app.workers.tasks.delete_document_task": {"queue": "documents"},
        "app.workers.tasks.generate_evaluation_task": {"queue": "evaluations"},
        "app.workers.tasks.grade_evaluation_task": {"queue": "evaluations"},
    },
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result configuration
    result_expires=3600,  # 1 hour
    result_extended=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Task tracking
    track_started=True,
    
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


# ===========================================
# Periodic tasks (if needed)
# ===========================================
celery_app.conf.beat_schedule = {
    # Example: cleanup old sessions every hour
    # "cleanup-old-sessions": {
    #     "task": "app.workers.tasks.cleanup_old_sessions",
    #     "schedule": 3600.0,  # 1 hour
    # },
}


# ===========================================
# Health check
# ===========================================
@celery_app.task(name="health_check")
def health_check() -> dict:
    """Health check para Celery."""
    return {
        "status": "ok",
        "service": "celery_worker"
    }