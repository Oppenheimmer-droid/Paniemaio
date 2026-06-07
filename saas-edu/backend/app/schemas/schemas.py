"""
Pydantic schemas para request/response de la API.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===========================================
# Base Schemas
# ===========================================
class TimestampMixin(BaseModel):
    """Mixin para campos de timestamp."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ===========================================
# Auth Schemas
# ===========================================
class TenantBase(BaseModel):
    """Base schema para tenant."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class TenantCreate(TenantBase):
    """Schema para crear tenant."""
    pass


class TenantResponse(TenantBase, TimestampMixin):
    """Schema de respuesta de tenant."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    settings_json: Optional[str] = "{}"


class UserBase(BaseModel):
    """Base schema para usuario."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema para registro de usuario."""
    password: str = Field(..., min_length=8, max_length=128)
    tenant_slug: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="student", pattern=r"^(admin|teacher|student)$")


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    password: str
    tenant_slug: str = Field(..., min_length=1, max_length=100)


class UserResponse(UserBase, TimestampMixin):
    """Schema de respuesta de usuario."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tenant_id: str
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None


class UserMeResponse(BaseModel):
    """Schema para /auth/me."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str
    tenant_name: str
    is_active: bool


class TokenResponse(BaseModel):
    """Schema para respuesta de tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AuthResponse(BaseModel):
    """Schema para respuesta completa de auth."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserMeResponse
    tenant: TenantResponse


class RefreshTokenRequest(BaseModel):
    """Schema para refresh token."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema para logout."""
    refresh_token: Optional[str] = None


class RegisterTenantRequest(BaseModel):
    """Schema para registrar nuevo tenant + admin."""
    tenant_name: str = Field(..., min_length=1, max_length=255)
    tenant_slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8, max_length=128)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)


# ===========================================
# Document Schemas
# ===========================================
class SubjectBase(BaseModel):
    """Base schema para materia."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    grade_levels: Optional[str] = None


class SubjectCreate(SubjectBase):
    """Schema para crear materia."""
    pass


class SubjectResponse(SubjectBase, TimestampMixin):
    """Schema de respuesta de materia."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tenant_id: str


class TopicBase(BaseModel):
    """Base schema para tema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)
    order_index: int = Field(default=0, ge=0)


class TopicCreate(TopicBase):
    """Schema para crear tema."""
    subject_id: str


class TopicResponse(TopicBase, TimestampMixin):
    """Schema de respuesta de tema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    subject_id: str


class DocumentBase(BaseModel):
    """Base schema para documento."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    subject_id: Optional[str] = None
    topic_id: Optional[str] = None
    difficulty: int = Field(default=1, ge=1, le=5)


class DocumentResponse(DocumentBase, TimestampMixin):
    """Schema de respuesta de documento."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tenant_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    page_count: int
    chunk_count: int
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    """Schema para lista de documentos."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentStatusResponse(BaseModel):
    """Schema para estado de documento."""
    id: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None


# ===========================================
# Chat Schemas
# ===========================================
class ChatSessionBase(BaseModel):
    """Base schema para sesión de chat."""
    title: str = Field(..., min_length=1, max_length=255)
    document_id: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    """Schema para crear sesión."""
    pass


class ChatSessionResponse(ChatSessionBase, TimestampMixin):
    """Schema de respuesta de sesión."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tenant_id: str
    user_id: str
    is_archived: bool
    message_count: int
    total_tokens: int
    last_message_at: Optional[datetime] = None


class ChatMessageResponse(BaseModel):
    """Schema de respuesta de mensaje."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_id: str
    role: str
    content: str
    citations: List[dict] = []
    tokens_used: int
    latency_ms: Optional[int] = None
    created_at: datetime


class CitationSchema(BaseModel):
    """Schema para citación."""
    source: str
    page: Optional[int] = None
    document_id: str
    text: str


class ChatQueryRequest(BaseModel):
    """Schema para consulta de chat."""
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    document_id: Optional[str] = None


class ChatQueryResponse(BaseModel):
    """Schema para respuesta de chat."""
    answer: str
    citations: List[CitationSchema] = []
    session_id: str
    tokens_used: int
    latency_ms: int


class ChatStreamResponse(BaseModel):
    """Schema para streaming de chat."""
    type: str  # "chunk", "citation", "done", "error"
    data: Any


# ===========================================
# Evaluation Schemas
# ===========================================
class EvaluationBase(BaseModel):
    """Base schema para evaluación."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    evaluation_type: str = Field(default="quiz", pattern=r"^(quiz|exam|practice)$")
    question_count: int = Field(default=5, ge=1, le=50)
    difficulty: int = Field(default=3, ge=1, le=5)
    time_limit_minutes: int = Field(default=30, ge=1)
    passing_score: int = Field(default=60, ge=0, le=100)


class EvaluationCreate(EvaluationBase):
    """Schema para crear evaluación."""
    document_id: str


class EvaluationResponse(EvaluationBase, TimestampMixin):
    """Schema de respuesta de evaluación."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tenant_id: str
    document_id: str
    created_by: str
    is_published: bool
    total_attempts: int
    avg_score: Optional[float] = None
    published_at: Optional[datetime] = None


class QuestionResponse(BaseModel):
    """Schema de respuesta de pregunta (sin correct_answer para students)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    evaluation_id: str
    question_text: str
    question_type: str
    options: List[str] = []
    explanation: Optional[str] = None
    difficulty: int
    points: int
    order_index: int


class EvaluationDetailResponse(BaseModel):
    """Schema para detalle de evaluación."""
    evaluation: EvaluationResponse
    questions: List[QuestionResponse]


class StartAttemptResponse(BaseModel):
    """Schema para iniciar intento."""
    attempt_id: str
    evaluation_id: str
    started_at: datetime
    time_limit_minutes: int


class SubmitAnswerRequest(BaseModel):
    """Schema para submit answer."""
    question_id: str
    answer_text: str


class SubmitAttemptRequest(BaseModel):
    """Schema para submit attempt."""
    answers: List[SubmitAnswerRequest]


class AnswerResponse(BaseModel):
    """Schema para respuesta."""
    model_config = ConfigDict(from_attributes=True)
    
    question_id: str
    answer_text: str
    is_correct: bool
    points_earned: int
    ai_grade_feedback: Optional[str] = None


class AttemptResultResponse(BaseModel):
    """Schema para resultado de intento."""
    model_config = ConfigDict(from_attributes=True)
    
    attempt_id: str
    evaluation_id: str
    score: float
    passed: bool
    total_points: int
    earned_points: int
    time_spent_seconds: int
    completed_at: datetime
    answers: List[AnswerResponse]


# ===========================================
# Analytics Schemas
# ===========================================
class AnalyticsOverviewResponse(BaseModel):
    """Schema para overview de analíticas."""
    total_documents: int
    active_students_7d: int
    messages_today: int
    avg_score: Optional[float] = None


class StudentProgressResponse(BaseModel):
    """Schema para progreso de estudiante."""
    user_id: str
    user_name: str
    email: str
    total_attempts: int
    avg_score: float
    last_activity: Optional[datetime] = None


class StudentProgressListResponse(BaseModel):
    """Schema para lista de progreso de estudiantes."""
    items: List[StudentProgressResponse]
    total: int


class DocumentUsageResponse(BaseModel):
    """Schema para uso de documento."""
    document_id: str
    title: str
    rag_queries: int
    evaluations: int
    chunks: int


class DocumentUsageListResponse(BaseModel):
    """Schema para lista de uso de documentos."""
    items: List[DocumentUsageResponse]
    total: int


# ===========================================
# Error Schemas
# ===========================================
class ErrorResponse(BaseModel):
    """Schema para errores."""
    code: str
    message: str
    detail: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema para errores de validación."""
    code: str = "VALIDATION_ERROR"
    message: str
    detail: List[dict] = []


# ===========================================
# Pagination
# ===========================================
class PaginationParams(BaseModel):
    """Parámetros de paginación."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Schema base para respuestas paginadas."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ===========================================
# Health
# ===========================================
class HealthResponse(BaseModel):
    """Schema para health check."""
    status: str
    app: str
    version: Optional[str] = "1.0.0"