"""
Tests para los modelos de datos.
"""

import pytest
from datetime import datetime

from app.models import (
    Tenant, User, RefreshToken,
    Subject, Topic, Document, DocumentChunk,
    ChatSession, ChatMessage,
    Evaluation, Question, EvaluationAttempt, Answer,
    TenantStatus, UserRole, DocumentStatus
)


class TestTenantModel:
    """Tests para el modelo Tenant."""
    
    def test_tenant_creation(self):
        """Verifica que se puede crear un tenant."""
        tenant = Tenant(
            id="test-id",
            name="Test Tenant",
            slug="test",
            status=TenantStatus.ACTIVE.value
        )
        assert tenant.name == "Test Tenant"
        assert tenant.slug == "test"
        assert tenant.status == "active"


class TestUserModel:
    """Tests para el modelo User."""
    
    def test_user_creation(self):
        """Verifica que se puede crear un usuario."""
        user = User(
            id="user-id",
            tenant_id="tenant-id",
            email="test@example.com",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
            role=UserRole.STUDENT.value
        )
        assert user.email == "test@example.com"
        assert user.role == "student"
        assert user.is_active is True


class TestDocumentModel:
    """Tests para el modelo Document."""
    
    def test_document_status_default(self):
        """Verifica el estado por defecto del documento."""
        doc = Document(
            id="doc-id",
            tenant_id="tenant-id",
            uploaded_by="user-id",
            filename="test.pdf",
            file_path="/uploads/test.pdf",
            title="Test Document"
        )
        assert doc.status == DocumentStatus.PENDING.value


class TestEvaluationModel:
    """Tests para el modelo Evaluation."""
    
    def test_evaluation_defaults(self):
        """Verifica los valores por defecto de una evaluación."""
        eval_obj = Evaluation(
            id="eval-id",
            tenant_id="tenant-id",
            document_id="doc-id",
            created_by="user-id",
            title="Test Quiz",
            question_count=10,
            difficulty=3,
            passing_score=70
        )
        assert eval_obj.is_published is False
        assert eval_obj.total_attempts == 0
        assert eval_obj.avg_score is None


# Pytest configuration
def pytest_configure(config):
    """Configuración de pytest."""
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")