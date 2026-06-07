"""
Funciones de seguridad: hashing de passwords y JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# ===========================================
# Password hashing
# ===========================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashea un password usando bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica un password contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ===========================================
# JWT tokens
# ===========================================
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un JWT access token.
    
    Args:
        data: Payload del token (debe incluir sub, role, tenant_id)
        expires_delta: Tiempo de expiración opcional
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    Crea un refresh token con expiración más larga.
    """
    data = {"sub": user_id, "type": "refresh"}
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    data.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    return jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


def verify_access_token(token: str) -> Optional[dict]:
    """
    Verifica y decodifica un access token.
    
    Returns:
        Payload del token o None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verifica un refresh token y devuelve el user_id.
    
    Returns:
        user_id o None si es inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except JWTError:
        return None