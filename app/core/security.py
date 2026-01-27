"""
Security Module
Handles password hashing, JWT token generation/validation, and authentication
"""
import hmac
import hashlib
from datetime import datetime, timedelta
from app.config import settings

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # return pwd_context.hash(password)
    password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Payload data to encode in token
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token
    
    Args:
        data: Payload data to encode in token
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a token is of the expected type
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type (access or refresh)
        
    Returns:
        True if token type matches
    """
    return payload.get("type") == expected_type


# security update with the generate download token
def generate_download_token(audio_id: int, user_id: int, expires_in_minutes: int = 60) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    expiry_str = expiry.strftime('%Y%m%d%H%M%S')

    message = f"{audio_id}:{user_id}:{expiry_str}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{audio_id}:{user_id}:{expiry_str}:{signature}"


def verify_download_token(token: str) -> tuple[int, int]:
    parts = token.split(":")
    if len(parts) != 4:
        raise ValueError("Invalid token format")

    audio_id, user_id, expiry_str, signature = parts
    expiry = datetime.strptime(expiry_str, "%Y%m%d%H%M%S")

    if datetime.utcnow() > expiry:
        raise ValueError("Token expired")

    message = f"{audio_id}:{user_id}:{expiry_str}"
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid signature")

    return int(audio_id), int(user_id)