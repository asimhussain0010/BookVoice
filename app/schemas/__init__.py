# app/schemas/__init__.py
"""
Pydantic schemas for request/response validation
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    TokenRefresh
)
from app.schemas.book import (
    BookBase,
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetail,
    BookListResponse
)
from app.schemas.audio import (
    AudioCreate,
    AudioResponse,
    AudioListResponse
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenRefresh",
    # Book schemas
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookDetail",
    "BookListResponse",
    # Audio schemas
    "AudioCreate",
    "AudioResponse",
    "AudioListResponse"
]
