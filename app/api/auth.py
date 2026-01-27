"""
Authentication API Endpoints
Handles user registration, login, logout, and token management

UPDATED:
- Added httpOnly cookie support for browser downloads
- Old token-only login logic preserved (commented)
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


# REGISTER 
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    """
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        is_active=True,
        is_verified=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# LOGIN
@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    response: Response,              # ✅ NEW
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access/refresh tokens

    UPDATED:
    - Sets httpOnly cookie for browser-based downloads
    - Still returns tokens in response body (backward compatible)
    """


    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login = datetime.utcnow()
    db.commit()

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username
    }

    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    # NEW: httpOnly Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,   # protects from XSS
        secure=not settings.DEBUG,  # HTTPS only in prod
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


# REFRESH TOKEN
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(token_data: TokenRefresh, response: Response, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token

    UPDATED:
    - Also refreshes httpOnly cookie
    """

    payload = decode_token(token_data.refresh_token)

    if not verify_token_type(payload, "refresh"):
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_payload = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username
    }

    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

# LOGOUT
@router.post("/logout")
def logout(response: Response):
    """
    Logout user

    UPDATED:
    - Clears authentication cookie
    """

    # return {"message": "Successfully logged out"}
    response.delete_cookie("access_token")

    return {"message": "Successfully logged out"}
