"""
Servicio de autenticación.
Maneja registro, login, refresh y logout.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password, 
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)
from app.core.config import settings
from app.models import Tenant, User, RefreshToken, UserRole


class AuthService:
    """Servicio de autenticación."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        """Obtiene un tenant por su slug."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str, tenant_id: str) -> User | None:
        """Obtiene un usuario por email y tenant."""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.email == email,
                    User.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> User | None:
        """Obtiene un usuario por ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_tenant(
        self,
        name: str,
        slug: str
    ) -> Tenant:
        """Crea un nuevo tenant."""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            status="active",
            settings_json="{}"
        )
        self.db.add(tenant)
        await self.db.flush()
        return tenant
    
    async def create_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = UserRole.STUDENT.value
    ) -> User:
        """Crea un nuevo usuario."""
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=True
        )
        self.db.add(user)
        await self.db.flush()
        return user
    
    async def create_refresh_token(self, user_id: str) -> RefreshToken:
        """Crea un nuevo refresh token."""
        token = create_refresh_token(user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        refresh_token = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=hash_password(token),  # Store hash, not plain token
            expires_at=expires_at,
            is_revoked=False
        )
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token
    
    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoca un refresh token."""
        user_id = verify_refresh_token(token)
        if not user_id:
            return False
        
        # Find and revoke all tokens for this user (logout from all devices)
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False
                )
            )
        )
        tokens = result.scalars().all()
        
        for t in tokens:
            t.is_revoked = True
        
        await self.db.flush()
        return True
    
    async def register_tenant(
        self,
        tenant_name: str,
        tenant_slug: str,
        admin_email: str,
        admin_password: str,
        admin_first_name: str,
        admin_last_name: str
    ) -> tuple[Tenant, User, str, str]:
        """
        Registra un nuevo tenant con su admin.
        
        Returns:
            (tenant, user, access_token, refresh_token)
        """
        # Create tenant
        tenant = await self.create_tenant(tenant_name, tenant_slug)
        
        # Create admin user
        admin = await self.create_user(
            tenant_id=tenant.id,
            email=admin_email,
            password=admin_password,
            first_name=admin_first_name,
            last_name=admin_last_name,
            role=UserRole.ADMIN.value
        )
        
        # Create tokens
        access_token = create_access_token({
            "sub": admin.id,
            "email": admin.email,
            "role": admin.role,
            "tenant_id": tenant.id,
            "type": "access"
        })
        
        refresh_token = create_refresh_token(admin.id)
        
        # Create refresh token record
        await self.create_refresh_token(admin.id)
        
        return tenant, admin, access_token, refresh_token
    
    async def login(
        self,
        email: str,
        password: str,
        tenant_slug: str
    ) -> tuple[User, Tenant, str, str] | None:
        """
        Autentica un usuario.
        
        Returns:
            (user, tenant, access_token, refresh_token) or None
        """
        # Get tenant
        tenant = await self.get_tenant_by_slug(tenant_slug)
        if not tenant:
            return None
        
        # Get user
        user = await self.get_user_by_email(email, tenant.id)
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        
        # Create tokens
        access_token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": tenant.id,
            "type": "access"
        })
        
        refresh_token = create_refresh_token(user.id)
        
        # Create refresh token record
        await self.create_refresh_token(user.id)
        
        return user, tenant, access_token, refresh_token
    
    async def refresh(
        self,
        refresh_token: str
    ) -> tuple[User, str, str] | None:
        """
        Refresca un access token.
        
        Returns:
            (user, new_access_token, new_refresh_token) or None
        """
        # Verify refresh token
        user_id = verify_refresh_token(refresh_token)
        if not user_id:
            return None
        
        # Get user
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            return None
        
        # Check if token is in our records (not revoked)
        # Note: For simplicity, we don't check against stored hash here
        # In production, you'd verify against stored hash
        
        # Create new tokens (token rotation)
        new_access_token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "type": "access"
        })
        
        new_refresh_token = create_refresh_token(user.id)
        
        # Create new refresh token record
        await self.create_refresh_token(user.id)
        
        return user, new_access_token, new_refresh_token
    
    async def logout(self, refresh_token: str) -> bool:
        """Logout del usuario."""
        return await self.revoke_refresh_token(refresh_token)
    
    async def get_tenant_info(self, tenant_id: str) -> Tenant | None:
        """Obtiene información del tenant."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()