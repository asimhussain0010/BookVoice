"""
Audio Generation API Endpoints
Handles audio conversion requests and status tracking
"""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.audio import AudioFile, AudioStatus
from app.schemas.audio import AudioResponse, AudioCreate, AudioListResponse
from app.dependencies import get_current_user
from app.tasks.audio_tasks import generate_audio_task
from app.config import settings

router = APIRouter(prefix="/audio", tags=["Audio"])


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


@router.get("/{audio_id}/download")
def download_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download generated audio file
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
    
    if audio_file.status != AudioStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio generation not completed yet"
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
    
    return FileResponse(
        path=audio_file.file_path,
        media_type="audio/mpeg",
        filename=audio_file.filename
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
        pass
    
    # Delete from database
    db.delete(audio_file)
    db.commit()
    
    return None