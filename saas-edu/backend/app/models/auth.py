"""
Modelos de autenticación y multi-tenant.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TenantStatus(str, PyEnum):
    """Estado del tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(str, PyEnum):
    """Rol del usuario."""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


# ===========================================
# Tenant (Multi-tenant)
# ===========================================
class Tenant(Base):
    """Tenant - representa una organización/cliente."""
    
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TenantStatus.ACTIVE.value
    )
    settings_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    subjects = relationship("Subject", back_populates="tenant", lazy="dynamic")
    documents = relationship("Document", back_populates="tenant", lazy="dynamic")
    chat_sessions = relationship("ChatSession", back_populates="tenant", lazy="dynamic")
    evaluation_attempts = relationship("EvaluationAttempt", back_populates="tenant", lazy="dynamic")


# ===========================================
# User
# ===========================================
class User(Base):
    """Usuario dentro de un tenant."""
    
    __tablename__ = "users"
    
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
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.STUDENT.value)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    uploaded_documents = relationship("Document", back_populates="uploaded_by_user")
    created_evaluations = relationship("Evaluation", back_populates="created_by_user")
    chat_sessions = relationship("ChatSession", back_populates="user", lazy="dynamic")
    evaluation_attempts = relationship("EvaluationAttempt", back_populates="user", lazy="dynamic")
    
    # Constraint: unique email per tenant
    __table_args__ = (
        # Note: MySQL doesn't support partial indexes, handled at app level
    )


# ===========================================
# RefreshToken
# ===========================================
class RefreshToken(Base):
    """Token de refresco para auth."""
    
    __tablename__ = "refresh_tokens"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")