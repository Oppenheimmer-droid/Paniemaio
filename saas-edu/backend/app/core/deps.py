"""
Dependencies para FastAPI: autenticación y autorización.
"""

from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token


# ===========================================
# Security scheme
# ===========================================
security = HTTPBearer()


# ===========================================
# Types
# ===========================================
class CurrentUser:
    """Usuario autenticado actual."""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        tenant_id: str,
        is_active: bool = True
    ):
        self.id = user_id
        self.email = email
        self.role = role
        self.tenant_id = tenant_id
        self.is_active = is_active


# ===========================================
# Dependencies
# ===========================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Dependency que obtiene el usuario actual desde el token JWT.
    
    Raises:
        401: Si el token es inválido o ha expirado
    """
    token = credentials.credentials
    
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Token inválido o expirado"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verificar que el token sea de acceso (no refresh)
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_TYPE",
                "message": "Se esperaba un access token"
            }
        )
    
    user = CurrentUser(
        user_id=payload.get("sub"),
        email=payload.get("email", ""),
        role=payload.get("role"),
        tenant_id=payload.get("tenant_id"),
        is_active=payload.get("is_active", True)
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_INACTIVE",
                "message": "Usuario desactivado"
            }
        )
    
    return user


def require_roles(*roles: str):
    """
    Dependency factory que verifica que el usuario tenga uno de los roles.
    
    Args:
        *roles: Roles permitidos (ej: "admin", "teacher", "student")
    
    Returns:
        Dependency function
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: CurrentUser = Depends(require_roles("admin"))):
            ...
    """
    async def role_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": f"Rol requerido: {', '.join(roles)}"
                }
            )
        return user
    
    return role_checker


# ===========================================
# Pre-built role dependencies
# ===========================================
async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Verifica que el usuario sea admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "message": "Se requiere rol de administrador"
            }
        )
    return user


async def require_teacher(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Verifica que el usuario sea teacher o admin."""
    if user.role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TEACHER_REQUIRED",
                "message": "Se requiere rol de profesor"
            }
        )
    return user


async def require_student_or_above(
    user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Verifica que el usuario sea student, teacher o admin."""
    return user  # Todos los roles autenticados pueden pasar


# ===========================================
# Optional user (para endpoints públicos)
# ===========================================
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db)
) -> Optional[CurrentUser]:
    """
    Obtiene el usuario actual si está autenticado, o None si no hay token.
    Para endpoints que funcionan tanto autenticados como anónimos.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None