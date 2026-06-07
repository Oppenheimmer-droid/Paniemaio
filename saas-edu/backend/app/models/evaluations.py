"""
Modelos de evaluaciones y quizzes.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EvaluationType(str, PyEnum):
    """Tipo de evaluación."""
    QUIZ = "quiz"
    EXAM = "exam"
    PRACTICE = "practice"


class QuestionType(str, PyEnum):
    """Tipo de pregunta."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


# ===========================================
# Evaluation
# ===========================================
class Evaluation(Base):
    """Evaluación o quiz generado automáticamente."""
    
    __tablename__ = "evaluations"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    evaluation_type: Mapped[str] = mapped_column(
        String(20),
        default=EvaluationType.QUIZ.value
    )
    
    # Config
    question_count: Mapped[int] = mapped_column(Integer, default=5)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=30)
    passing_score: Mapped[int] = mapped_column(Integer, default=60)  # percentage
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Stats
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    avg_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates=None)  # Will define via back_populates
    document = relationship("Document", back_populates="evaluations")
    created_by_user = relationship("User", back_populates="created_evaluations")
    questions = relationship("Question", back_populates="evaluation", lazy="dynamic", cascade="all, delete-orphan")
    attempts = relationship("EvaluationAttempt", back_populates="evaluation", lazy="dynamic")


# ===========================================
# Question
# ===========================================
class Question(Base):
    """Pregunta dentro de una evaluación."""
    
    __tablename__ = "questions"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    evaluation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(20),
        default=QuestionType.MULTIPLE_CHOICE.value
    )
    
    # Options (JSON array for multiple choice)
    options: Mapped[dict] = mapped_column(JSON, default=list)
    
    # Correct answer (JSON - index for MC, boolean for T/F, text for short)
    correct_answer: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Additional info
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)
    points: Mapped[int] = mapped_column(Integer, default=1)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    # Source info
    source_chunk_id: Mapped[str] = mapped_column(String(36), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="questions")
    answers = relationship("Answer", back_populates="question", lazy="dynamic", cascade="all, delete-orphan")


# ===========================================
# EvaluationAttempt
# ===========================================
class EvaluationAttempt(Base):
    """Intento de un estudiante de hacer una evaluación."""
    
    __tablename__ = "evaluation_attempts"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    evaluation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Results
    score: Mapped[float] = mapped_column(Float, default=0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="evaluation_attempts")
    evaluation = relationship("Evaluation", back_populates="attempts")
    user = relationship("User", back_populates="evaluation_attempts")
    answers = relationship("Answer", back_populates="attempt", lazy="dynamic", cascade="all, delete-orphan")


# ===========================================
# Answer
# ===========================================
class Answer(Base):
    """Respuesta de un estudiante a una pregunta."""
    
    __tablename__ = "answers"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    attempt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("evaluation_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Student's answer
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Grading
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    
    # AI Feedback (for short answer)
    ai_grade_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    attempt = relationship("EvaluationAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")