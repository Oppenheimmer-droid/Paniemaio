"""
Servicio de Analíticas.
Dashboard de métricas para teachers/admins.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Document, ChatSession, ChatMessage, 
    Evaluation, EvaluationAttempt, User
)


class AnalyticsService:
    """Servicio de analíticas."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_overview(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene overview de analíticas."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total documents
        docs_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        )
        total_documents = docs_result.scalar() or 0
        
        # Active students (7 days)
        active_result = await self.db.execute(
            select(func.count(func.distinct(ChatSession.user_id)))
            .where(
                and_(
                    ChatSession.tenant_id == tenant_id,
                    ChatSession.last_message_at >= week_ago
                )
            )
        )
        active_students = active_result.scalar() or 0
        
        # Messages today
        messages_result = await self.db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(
                and_(
                    ChatSession.tenant_id == tenant_id,
                    ChatMessage.created_at >= today_start
                )
            )
        )
        messages_today = messages_result.scalar() or 0
        
        # Average score
        score_result = await self.db.execute(
            select(func.avg(EvaluationAttempt.score))
            .where(
                and_(
                    EvaluationAttempt.tenant_id == tenant_id,
                    EvaluationAttempt.completed_at.isnot(None)
                )
            )
        )
        avg_score = score_result.scalar()
        if avg_score:
            avg_score = round(avg_score, 1)
        
        return {
            "total_documents": total_documents,
            "active_students_7d": active_students,
            "messages_today": messages_today,
            "avg_score": avg_score
        }
    
    async def get_students_progress(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Obtiene progreso de estudiantes."""
        # Subquery for student stats
        subquery = (
            select(
                EvaluationAttempt.user_id,
                func.count(EvaluationAttempt.id).label("total_attempts"),
                func.avg(EvaluationAttempt.score).label("avg_score"),
                func.max(EvaluationAttempt.completed_at).label("last_activity")
            )
            .where(
                and_(
                    EvaluationAttempt.tenant_id == tenant_id,
                    EvaluationAttempt.completed_at.isnot(None)
                )
            )
            .group_by(EvaluationAttempt.user_id)
        ).subquery()
        
        # Join with users
        query = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                subquery.c.total_attempts,
                subquery.c.avg_score,
                subquery.c.last_activity
            )
            .join(subquery, User.id == subquery.c.user_id)
            .where(User.tenant_id == tenant_id)
            .order_by(desc(subquery.c.last_activity))
        )
        
        # Count
        count_query = select(func.count(User.id)).where(
            User.tenant_id == tenant_id,
            User.role == "student"
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        students = []
        for row in rows:
            students.append({
                "user_id": row.id,
                "user_name": f"{row.first_name} {row.last_name}",
                "email": row.email,
                "total_attempts": row.total_attempts or 0,
                "avg_score": round(row.avg_score, 1) if row.avg_score else None,
                "last_activity": row.last_activity
            })
        
        return students, total
    
    async def get_documents_usage(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Obtiene uso de documentos."""
        # Get documents with stats
        query = (
            select(
                Document.id,
                Document.title,
                func.count(ChatMessage.id).label("rag_queries"),
                func.count(func.distinct(Evaluation.id)).label("evaluations"),
                func.sum(Document.chunk_count).label("chunks")
            )
            .outerjoin(ChatSession, Document.id == ChatSession.document_id)
            .outerjoin(ChatMessage, ChatSession.id == ChatMessage.session_id)
            .outerjoin(Evaluation, Document.id == Evaluation.document_id)
            .where(Document.tenant_id == tenant_id)
            .group_by(Document.id)
            .order_by(desc("rag_queries"))
        )
        
        # Count
        count_query = select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        documents = []
        for row in rows:
            documents.append({
                "document_id": row.id,
                "title": row.title,
                "rag_queries": row.rag_queries or 0,
                "evaluations": row.evaluations or 0,
                "chunks": row.chunks or 0
            })
        
        return documents, total
    
    async def get_user_stats(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un usuario específico."""
        # Total attempts
        attempts_result = await self.db.execute(
            select(func.count(EvaluationAttempt.id))
            .where(
                and_(
                    EvaluationAttempt.user_id == user_id,
                    EvaluationAttempt.tenant_id == tenant_id
                )
            )
        )
        total_attempts = attempts_result.scalar() or 0
        
        # Avg score
        score_result = await self.db.execute(
            select(func.avg(EvaluationAttempt.score))
            .where(
                and_(
                    EvaluationAttempt.user_id == user_id,
                    EvaluationAttempt.tenant_id == tenant_id,
                    EvaluationAttempt.completed_at.isnot(None)
                )
            )
        )
        avg_score = score_result.scalar()
        if avg_score:
            avg_score = round(avg_score, 1)
        
        # Last activity
        last_result = await self.db.execute(
            select(func.max(EvaluationAttempt.completed_at))
            .where(
                and_(
                    EvaluationAttempt.user_id == user_id,
                    EvaluationAttempt.tenant_id == tenant_id
                )
            )
        )
        last_activity = last_result.scalar()
        
        # Chat sessions
        sessions_result = await self.db.execute(
            select(func.count(ChatSession.id))
            .where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.tenant_id == tenant_id
                )
            )
        )
        chat_sessions = sessions_result.scalar() or 0
        
        return {
            "total_attempts": total_attempts,
            "avg_score": avg_score,
            "last_activity": last_activity,
            "chat_sessions": chat_sessions
        }