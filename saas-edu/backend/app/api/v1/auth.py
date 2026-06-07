"""
API Endpoints de autenticación.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, CurrentUser
from app.core.config import settings
from app.services.auth_service import AuthService
from app.schemas.schemas import (
    RegisterTenantRequest,
    UserLogin,
    RefreshTokenRequest,
    LogoutRequest,
    AuthResponse,
    TokenResponse,
    UserMeResponse,
    ErrorResponse,
)


router = APIRouter(prefix="/auth", tags=["Autenticación"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency para AuthService."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"model": ErrorResponse, "description": "Datos inválidos"},
        409: {"model": ErrorResponse, "description": "Tenant o email ya existe"},
    },
    summary="Registrar nuevo tenant y admin",
    description="Crea un nuevo tenant con su administrador inicial."
)
async def register_tenant(
    request: RegisterTenantRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Registra un nuevo tenant con su admin."""
    # Check if tenant slug already exists
    existing_tenant = await auth_service.get_tenant_by_slug(request.tenant_slug)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TENANT_EXISTS",
                "message": f"El slug '{request.tenant_slug}' ya está en uso"
            }
        )
    
    try:
        tenant, user, access_token, refresh_token = await auth_service.register_tenant(
            tenant_name=request.tenant_name,
            tenant_slug=request.tenant_slug,
            admin_email=request.admin_email,
            admin_password=request.admin_password,
            admin_first_name=request.admin_first_name,
            admin_last_name=request.admin_last_name
        )
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserMeResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                is_active=user.is_active
            ),
            tenant={
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "settings_json": tenant.settings_json,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at
            } if hasattr(tenant, 'to_dict') else {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "settings_json": tenant.settings_json,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "REGISTRATION_FAILED",
                "message": str(e)
            }
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        200: {"description": "Login exitoso"},
        401: {"model": ErrorResponse, "description": "Credenciales inválidas"},
        404: {"model": ErrorResponse, "description": "Tenant no encontrado"},
    },
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve tokens JWT."
)
async def login(
    request: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint de login."""
    result = await auth_service.login(
        email=request.email,
        password=request.password,
        tenant_slug=request.tenant_slug
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Email, contraseña o tenant incorrecto"
            }
        )
    
    user, tenant, access_token, refresh_token = result
    
    # Build tenant response dict
    tenant_dict = {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "status": tenant.status,
        "settings_json": tenant.settings_json,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at
    }
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserMeResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            is_active=user.is_active
        ),
        tenant=tenant_dict
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        200: {"description": "Token refrescado"},
        401: {"model": ErrorResponse, "description": "Refresh token inválido"},
    },
    summary="Refrescar access token",
    description="Usa un refresh token para obtener un nuevo access token."
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint para refrescar tokens."""
    result = await auth_service.refresh(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_REFRESH_TOKEN",
                "message": "El refresh token es inválido o ha expirado"
            }
        )
    
    user, new_access_token, new_refresh_token = result
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Logout exitoso"},
        401: {"model": ErrorResponse, "description": "Token inválido"},
    },
    summary="Cerrar sesión",
    description="Invalida el refresh token del usuario."
)
async def logout(
    request: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint de logout."""
    if request.refresh_token:
        await auth_service.logout(request.refresh_token)
    
    return None


@router.get(
    "/me",
    response_model=UserMeResponse,
    responses={
        200: {"description": "Usuario actual"},
        401: {"model": ErrorResponse, "description": "No autenticado"},
    },
    summary="Obtener usuario actual",
    description="Devuelve la información del usuario autenticado."
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint para obtener el usuario actual."""
    tenant = await auth_service.get_tenant_info(current_user.tenant_id)
    
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        tenant_name=tenant.name if tenant else "Unknown",
        is_active=current_user.is_active
    )


@router.get(
    "/health",
    tags=["Health"],
    summary="Health check de auth"
)
async def auth_health():
    """Health check endpoint."""
    return {"status": "ok", "service": "auth"}