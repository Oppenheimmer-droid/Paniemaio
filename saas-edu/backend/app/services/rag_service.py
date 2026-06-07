"""
RAG Service — Chat con citaciones usando Groq.
"""

import uuid
import json
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from groq import Groq
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatSession, ChatMessage, Document
from app.rag.vector_store import retrieval_pipeline, RetrievedChunk
from app.core.config import settings


# System prompt obligatorio (no modificar)
SYSTEM_PROMPT = """Eres un tutor académico. Responde ÚNICAMENTE basándote en el contexto proporcionado.
Cita las fuentes usando [Fuente N] donde N es el número de fuente.
Si el contexto no contiene la respuesta, dilo claramente: "No encontré información sobre esto en los documentos."
Sé pedagógico, claro y conciso. Si hay números de página, inclúyelos."""


class CitationSchema:
    """Schema para citación."""
    def __init__(self, source: str, page: Optional[int], document_id: str, text: str):
        self.source = source
        self.page = page
        self.document_id = document_id
        self.text = text

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "page": self.page,
            "document_id": self.document_id,
            "text": self.text[:200]  # Truncar para guardar
        }


class RAGService:
    """Servicio de Retrieval Augmented Generation para chat."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
    
    async def create_session(
        self,
        tenant_id: str,
        user_id: str,
        title: str,
        document_id: Optional[str] = None
    ) -> ChatSession:
        """Crea una nueva sesión de chat."""
        session = ChatSession(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            document_id=document_id,
            title=title,
            is_archived=False,
            message_count=0,
            total_tokens=0
        )
        
        self.db.add(session)
        await self.db.flush()
        
        return session
    
    async def get_session(
        self,
        session_id: str,
        tenant_id: str
    ) -> Optional[ChatSession]:
        """Obtiene una sesión de chat."""
        result = await self.db.execute(
            select(ChatSession).where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_sessions(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ChatSession], int]:
        """Lista sesiones de chat."""
        query = select(ChatSession).where(ChatSession.tenant_id == tenant_id)
        
        if user_id:
            query = query.where(ChatSession.user_id == user_id)
        
        query = query.where(ChatSession.is_archived == False)
        query = query.order_by(ChatSession.last_message_at.desc())
        
        # Count
        from sqlalchemy import func
        count_query = select(func.count(ChatSession.id)).where(
            ChatSession.tenant_id == tenant_id,
            ChatSession.is_archived == False
        )
        if user_id:
            count_query = count_query.where(ChatSession.user_id == user_id)
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        return list(sessions), total
    
    async def get_messages(
        self,
        session_id: str,
        tenant_id: str
    ) -> List[ChatMessage]:
        """Obtiene mensajes de una sesión."""
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())
    
    async def query(
        self,
        tenant_id: str,
        user_id: str,
        question: str,
        session_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa una pregunta RAG y devuelve respuesta con citaciones.
        
        Args:
            tenant_id: ID del tenant
            user_id: ID del usuario
            question: Pregunta del usuario
            session_id: ID de sesión (opcional)
            document_id: Filtrar por documento específico
            
        Returns:
            Dict con answer, citations, session_id, tokens_used, latency_ms
        """
        start_time = time.time()
        
        # 1. Retrieve relevant chunks
        chunks = retrieval_pipeline.retrieve(
            tenant_id=tenant_id,
            query=question,
            top_k=5,
            filter_document_id=document_id
        )
        
        if not chunks:
            return {
                "answer": "No encontré información sobre esto en los documentos. "
                         "Asegúrate de que los documentos estén procesados antes de preguntar.",
                "citations": [],
                "session_id": session_id,
                "tokens_used": 0,
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        
        # 2. Build context with citations
        context = self._build_context(chunks)
        
        # 3. Call Groq
        answer, tokens_used = self._call_groq(question, context)
        
        # 4. Build citations
        citations = self._build_citations(chunks)
        
        # 5. Save messages to session
        latency_ms = int((time.time() - start_time) * 1000)
        
        if session_id:
            await self._save_messages(
                session_id=session_id,
                user_question=question,
                assistant_answer=answer,
                citations=citations,
                tokens_used=tokens_used,
                latency_ms=latency_ms
            )
        
        return {
            "answer": answer,
            "citations": [c.to_dict() for c in citations],
            "session_id": session_id,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms
        }
    
    def _build_context(self, chunks: List[RetrievedChunk]) -> str:
        """Construye contexto para el LLM."""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            page_info = f" (página {chunk.page_number})" if chunk.page_number else ""
            context_parts.append(
                f"[Fuente {i+1}]{page_info}: {chunk.content}"
            )
        
        return "\n\n".join(context_parts)
    
    def _build_citations(self, chunks: List[RetrievedChunk]) -> List[CitationSchema]:
        """Construye objetos de citación."""
        citations = []
        
        for i, chunk in enumerate(chunks):
            # Get document title
            doc_title = f"Documento {chunk.document_id}"
            
            citations.append(CitationSchema(
                source=f"[Fuente {i+1}]",
                page=chunk.page_number,
                document_id=chunk.document_id,
                text=chunk.content[:300]
            ))
        
        return citations
    
    def _call_groq(self, question: str, context: str) -> Tuple[str, int]:
        """Llama a Groq LLM."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
        
        return answer, tokens_used
    
    async def _save_messages(
        self,
        session_id: str,
        user_question: str,
        assistant_answer: str,
        citations: List[CitationSchema],
        tokens_used: int,
        latency_ms: int
    ):
        """Guarda los mensajes en la base de datos."""
        # User message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_question,
            citations=[],
            tokens_used=0,
            latency_ms=None
        )
        self.db.add(user_msg)
        
        # Assistant message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_answer,
            citations=[c.to_dict() for c in citations],
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            model=settings.GROQ_MODEL
        )
        self.db.add(assistant_msg)
        
        # Update session stats
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.message_count += 2
            session.total_tokens += tokens_used
            session.last_message_at = datetime.utcnow()
        
        await self.db.flush()
    
    async def stream_query(
        self,
        tenant_id: str,
        user_id: str,
        question: str,
        session_id: Optional[str] = None
    ):
        """
        Versión streaming del query (generador para SSE).
        
        Yields:
            Dicts con {type, data}
        """
        # Similar a query pero con yield
        chunks = retrieval_pipeline.retrieve(
            tenant_id=tenant_id,
            query=question,
            top_k=5
        )
        
        if not chunks:
            yield {"type": "done", "data": "No encontré información."}
            return
        
        context = self._build_context(chunks)
        
        # Call Groq con streaming
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"}
        ]
        
        response = self.groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
            stream=True
        )
        
        full_answer = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_answer += text
                yield {"type": "chunk", "data": text}
        
        yield {"type": "done", "data": full_answer}
        yield {"type": "citations", "data": [c.to_dict() for c in self._build_citations(chunks)]}