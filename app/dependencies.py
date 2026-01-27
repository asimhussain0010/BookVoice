# """
# FastAPI Dependencies
# Reusable dependency functions for authentication, authorization, etc.
# """

# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from sqlalchemy.orm import Session
# from app.database import get_db
# from app.models.user import User
# from app.core.security import decode_token, verify_token_type

# # Security scheme for Swagger UI
# security = HTTPBearer()


# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ) -> User:
#     """
#     Dependency to get current authenticated user from JWT token
    
#     Usage:
#         @app.get("/protected")
#         def protected_route(current_user: User = Depends(get_current_user)):
#             return {"user_id": current_user.id}
#     """
#     token = credentials.credentials
    
#     # Decode and validate token
#     payload = decode_token(token)
    
#     # Verify it's an access token
#     if not verify_token_type(payload, "access"):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token type",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     # Get user from database
#     user_id = int(payload.get("sub"))
#     user = db.query(User).filter(User.id == user_id).first()
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Inactive user"
#         )
    
#     return user


# def get_current_active_user(
#     current_user: User = Depends(get_current_user)
# ) -> User:
#     """
#     Dependency to ensure user is active
#     """
#     if not current_user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Inactive user"
#         )
#     return current_user


# def get_current_superuser(
#     current_user: User = Depends(get_current_user)
# ) -> User:
#     """
#     Dependency to ensure user is a superuser
#     """
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not enough permissions"
#         )
#     return current_user



"""
FastAPI Dependencies
Reusable dependency functions for authentication, authorization, etc.

UPDATED:
- Added optional authentication (header OR cookie)
- Added cookie-based auth for browser downloads
- Existing header-based JWT auth preserved
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import decode_token, verify_token_type


# =====================================================
# SECURITY SCHEMES
# =====================================================

# OLD (strict – raises error if no Authorization header)
security = HTTPBearer()

# NEW (optional – does NOT raise error if missing)
security_optional = HTTPBearer(auto_error=False)


# =====================================================
# STRICT AUTH (UNCHANGED)
# =====================================================
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    STRICT authentication using Authorization header (Bearer token)

    Used for protected API routes
    """

    token = credentials.credentials

    payload = decode_token(token)

    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user


# =====================================================
# OPTIONAL AUTH (NEW)
# =====================================================
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    OPTIONAL authentication

    - Returns User if Authorization header is present
    - Returns None if no authentication provided
    """

    if not credentials:
        return None

    try:
        payload = decode_token(credentials.credentials)

        if not verify_token_type(payload, "access"):
            return None

        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            return None

        return user
    except Exception:
        return None


# =====================================================
# COOKIE-BASED AUTH (NEW)
# =====================================================
def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Authentication using httpOnly cookie

    Used for browser downloads where headers cannot be set
    """

    if not access_token:
        return None

    # Remove "Bearer " prefix
    token = access_token.replace("Bearer ", "")

    try:
        payload = decode_token(token)

        if not verify_token_type(payload, "access"):
            return None

        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()

        return user if user and user.is_active else None
    except Exception:
        return None


# =====================================================
# ACTIVE USER CHECK (UNCHANGED)
# =====================================================
def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user is active
    """
    return current_user


# =====================================================
# SUPERUSER CHECK (UNCHANGED)
# =====================================================
def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user is a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
