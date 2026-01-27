"""
Audio Generation API Endpoints - COMPLETE FIXED VERSION
Handles audio conversion requests and downloads with proper authentication
"""

import os
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.audio import AudioFile, AudioStatus
from app.schemas.audio import AudioResponse, AudioCreate, AudioListResponse
from app.dependencies import get_current_user
from app.tasks.audio_tasks import generate_audio_task
from app.config import settings
from app.core.security import decode_token, verify_token_type

router = APIRouter(prefix="/audio", tags=["Audio"])

# Optional security (doesn't raise error if no token)
security_optional = HTTPBearer(auto_error=False)


# HELPER FUNCTIONS FOR SIGNED DOWNLOAD TOKENS
def generate_download_token(audio_id: int, user_id: int, expires_in_minutes: int = 60) -> str:
    """
    Generate a temporary signed token for downloading
    
    Args:
        audio_id: Audio file ID
        user_id: User ID
        expires_in_minutes: Token validity period (default 60 minutes)
        
    Returns:
        Signed token string
    """
    expiry = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    expiry_str = expiry.strftime('%Y%m%d%H%M%S')
    
    # Create message and signature
    message = f"{audio_id}:{user_id}:{expiry_str}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Return token: audioId:userId:expiry:signature
    return f"{audio_id}:{user_id}:{expiry_str}:{signature}"


def verify_download_token(token: str) -> tuple:
    """
    Verify download token and return audio_id, user_id
    
    Args:
        token: Signed token string
        
    Returns:
        Tuple of (audio_id, user_id)
        
    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        parts = token.split(':')
        if len(parts) != 4:
            raise ValueError("Invalid token format")
        
        audio_id, user_id, expiry_str, signature = parts
        
        # Check if token is expired
        expiry = datetime.strptime(expiry_str, '%Y%m%d%H%M%S')
        if datetime.utcnow() > expiry:
            raise ValueError("Token has expired")
        
        # Verify signature
        message = f"{audio_id}:{user_id}:{expiry_str}"
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")
        
        return int(audio_id), int(user_id)
        
    except Exception as e:
        raise ValueError(f"Invalid or expired token: {str(e)}")


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns None if not authenticated
    Used for endpoints that support multiple auth methods
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if not verify_token_type(payload, "access"):
            return None
        
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return None
        
        return user
    except:
        return None


# AUDIO GENERATION ENDPOINTS
@router.post("/generate", response_model=AudioResponse, status_code=status.HTTP_201_CREATED)
def generate_audio(
    audio_data: AudioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate audio from a book
    
    - Creates audio file record
    - Starts background Celery task
    - Returns task information for tracking
    """
    # Verify book exists and belongs to user
    book = db.query(Book).filter(
        Book.id == audio_data.book_id,
        Book.user_id == current_user.id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if not book.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book has no content to convert"
        )
    
    # Create audio file record
    audio_file = AudioFile(
        user_id=current_user.id,
        book_id=book.id,
        filename=f"{book.title.replace(' ', '_')}_audio.mp3",
        file_path="",  # Will be set by task
        language=audio_data.language or book.language,
        voice=audio_data.voice,
        speed=audio_data.speed,
        status=AudioStatus.PENDING
    )
    
    db.add(audio_file)
    db.commit()
    db.refresh(audio_file)
    
    # Start background task
    task = generate_audio_task.delay(
        audio_id=audio_file.id,
        book_id=book.id,
        language=audio_file.language
    )
    
    # Update with task ID
    audio_file.task_id = task.id
    db.commit()
    db.refresh(audio_file)
    
    return audio_file


@router.get("/", response_model=AudioListResponse)
def get_audio_files(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's audio files
    """
    skip = (page - 1) * page_size
    
    query = db.query(AudioFile).filter(AudioFile.user_id == current_user.id)
    total = query.count()
    audio_files = query.order_by(AudioFile.created_at.desc()).offset(skip).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": audio_files,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{audio_id}", response_model=AudioResponse)
def get_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about a specific audio file
    """
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == audio_id,
        AudioFile.user_id == current_user.id
    ).first()
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return audio_file


@router.get("/{audio_id}/status")
def get_audio_status(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time status of audio generation
    """
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == audio_id,
        AudioFile.user_id == current_user.id
    ).first()
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return {
        "id": audio_file.id,
        "status": audio_file.status,
        "progress": audio_file.progress,
        "error_message": audio_file.error_message
    }


# DOWNLOAD ENDPOINTS - FIXED VERSION
@router.get("/{audio_id}/download-url")
def get_download_url(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a temporary signed URL for downloading audio
    
    Returns a URL that's valid for 60 minutes
    This URL can be used in browser without authentication header
    
    Example response:
    {
        "download_url": "/api/v1/audio/4/download?token=4:1:20260121100000:abc123...",
        "expires_in_minutes": 60,
        "expires_at": "2026-01-21T10:00:00"
    }
    """
    # Verify audio exists and belongs to user
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == audio_id,
        AudioFile.user_id == current_user.id
    ).first()
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    if audio_file.status != AudioStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio generation not completed yet"
        )
    
    # Generate signed token (valid for 60 minutes)
    token = generate_download_token(audio_id, current_user.id, expires_in_minutes=60)
    
    # Return download URL with token
    return {
        "download_url": f"/api/v1/audio/{audio_id}/download?token={token}",
        "expires_in_minutes": 60,
        "expires_at": (datetime.utcnow() + timedelta(minutes=60)).isoformat()
    }


@router.get("/{audio_id}/download")
def download_audio(
    audio_id: int,
    token: Optional[str] = Query(None, description="Temporary download token"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Download generated audio file
    
    Supports two authentication methods:
    1. Bearer token in Authorization header (for API calls)
    2. Signed token in query parameter (for browser downloads)
    
    Usage:
    - API: GET /audio/4/download (with Authorization: Bearer <token>)
    - Browser: GET /audio/4/download?token=<signed-token>
    """
    user_id = None
    
    # Method 1: Signed token authentication (for browser downloads)
    if token:
        try:
            token_audio_id, token_user_id = verify_download_token(token)
            
            # Verify audio_id matches token
            if token_audio_id != audio_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token for this audio file"
                )
            
            user_id = token_user_id
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )
    
    # Method 2: JWT Bearer token authentication (for API calls)
    elif current_user:
        user_id = current_user.id
    
    # No authentication provided
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use Bearer token or get a signed download URL from /audio/{id}/download-url endpoint",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get audio file
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == audio_id,
        AudioFile.user_id == user_id
    ).first()
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    if audio_file.status != AudioStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio is not ready for download. Current status: {audio_file.status}"
        )
    
    if not os.path.exists(audio_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found on disk"
        )
    
    # Update download statistics
    audio_file.is_downloaded = True
    audio_file.download_count += 1
    db.commit()
    
    # Return file for download
    return FileResponse(
        path=audio_file.file_path,
        media_type="audio/mpeg",
        filename=audio_file.filename,
        headers={
            "Content-Disposition": f'attachment; filename="{audio_file.filename}"'
        }
    )


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an audio file
    """
    audio_file = db.query(AudioFile).filter(
        AudioFile.id == audio_id,
        AudioFile.user_id == current_user.id
    ).first()
    
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(audio_file.file_path):
            os.remove(audio_file.file_path)
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Delete from database
    db.delete(audio_file)
    db.commit()
    
    return None