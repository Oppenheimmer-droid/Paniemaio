"""Models module — re-exports all SQLAlchemy models."""

from app.models.auth import (
    Tenant, User, RefreshToken, TenantStatus, UserRole,
)
from app.models.documents import (
    Subject, Topic, Document, DocumentChunk, DocumentStatus,
)
from app.models.chat import (ChatSession, ChatMessage)
from app.models.evaluations import (
    Evaluation, Question, EvaluationAttempt, Answer,
    EvaluationType, QuestionType,
)

__all__ = [
    "Tenant", "User", "RefreshToken", "TenantStatus", "UserRole",
    "Subject", "Topic", "Document", "DocumentChunk", "DocumentStatus",
    "ChatSession", "ChatMessage",
    "Evaluation", "Question", "EvaluationAttempt", "Answer",
    "EvaluationType", "QuestionType",
]
