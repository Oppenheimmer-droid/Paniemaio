"""
Tests para autenticación.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.auth_service import AuthService
from app.core.security import hash_password, verify_password


class TestPasswordHashing:
    """Tests para hashing de passwords."""
    
    def test_hash_password_creates_hash(self):
        """Verifica que hash_password crea un hash."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Verifica password correcto."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Verifica password incorrecto."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Verifica que diferentes passwords generan diferentes hashes."""
        hash1 = hash_password("Password1")
        hash2 = hash_password("Password2")
        
        assert hash1 != hash2


class TestAuthService:
    """Tests para AuthService."""
    
    @pytest.fixture
    def mock_db(self):
        """Crea un mock de la sesión de DB."""
        return AsyncMock()
    
    @pytest.fixture
    def auth_service(self, mock_db):
        """Crea una instancia de AuthService."""
        return AuthService(mock_db)
    
    def test_service_initialization(self, auth_service):
        """Verifica que el servicio se inicializa correctamente."""
        assert auth_service is not None
        assert auth_service.db is not None


class TestAuthEndpoints:
    """Tests para endpoints de auth."""
    
    def test_login_schema_validation(self):
        """Verifica el schema de login."""
        from app.schemas.schemas import UserLogin
        
        # Valid email and password
        login = UserLogin(
            email="test@example.com",
            password="password123",
            tenant_slug="test-tenant"
        )
        
        assert login.email == "test@example.com"
        assert login.password == "password123"
        assert login.tenant_slug == "test-tenant"
    
    def test_register_schema_validation(self):
        """Verifica el schema de registro."""
        from app.schemas.schemas import RegisterTenantRequest
        
        register = RegisterTenantRequest(
            tenant_name="Test Org",
            tenant_slug="test-org",
            admin_email="admin@test.com",
            admin_password="password123",
            admin_first_name="Admin",
            admin_last_name="User"
        )
        
        assert register.tenant_name == "Test Org"
        assert register.admin_email == "admin@test.com"


class TestTokenCreation:
    """Tests para creación de tokens."""
    
    def test_access_token_creation(self):
        """Verifica creación de access token."""
        from app.core.security import create_access_token
        
        data = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "admin",
            "tenant_id": "tenant-123",
            "type": "access"
        }
        
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_refresh_token_creation(self):
        """Verifica creación de refresh token."""
        from app.core.security import create_refresh_token
        
        user_id = "user-123"
        token = create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_access_token_verification(self):
        """Verifica verificación de access token."""
        from app.core.security import create_access_token, verify_access_token
        
        data = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "admin",
            "tenant_id": "tenant-123",
            "type": "access"
        }
        
        token = create_access_token(data)
        payload = verify_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "admin"
    
    def test_invalid_token_verification(self):
        """Verifica que tokens inválidos devuelven None."""
        from app.core.security import verify_access_token
        
        payload = verify_access_token("invalid-token")
        
        assert payload is None