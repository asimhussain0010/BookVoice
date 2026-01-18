"""
Book Management API Endpoints
Handles book upload, retrieval, update, and deletion
"""

import os
import shutil
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models.user import User
from app.models.book import Book, BookStatus
from app.schemas.book import BookResponse, BookDetail, BookListResponse, BookUpdate
from app.dependencies import get_current_user
from app.services.text_extractor import TextExtractor
from app.config import settings

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/upload", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: str = Form(None),
    language: str = Form("en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a book file
    
    - Validates file type and size
    - Saves file to disk
    - Extracts text content
    - Creates book record
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().timestamp()
    filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Check file size
    if file_size > settings.MAX_UPLOAD_SIZE:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
        )
    
    # Create book record
    book = Book(
        user_id=current_user.id,
        title=title,
        author=author,
        language=language,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_ext.replace('.', ''),
        status=BookStatus.PROCESSING
    )
    
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # Extract text in background
    try:
        extractor = TextExtractor()
        text, word_count, char_count = extractor.extract(file_path, file_ext)
        
        # Update book with extracted content
        book.content = text
        book.word_count = word_count
        book.character_count = char_count
        book.status = BookStatus.READY
        book.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(book)
        
    except Exception as e:
        book.status = BookStatus.ERROR
        book.error_message = str(e)
        db.commit()
        db.refresh(book)
    
    return book


@router.get("/", response_model=BookListResponse)
def get_books(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of user's books
    """
    # Calculate pagination
    skip = (page - 1) * page_size
    
    # Query books
    query = db.query(Book).filter(Book.user_id == current_user.id)
    total = query.count()
    books = query.order_by(Book.created_at.desc()).offset(skip).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": books,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/{book_id}", response_model=BookDetail)
def get_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific book
    """
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Create preview of content
    extractor = TextExtractor()
    content_preview = extractor.preview_text(book.content) if book.content else None
    
    book_dict = {
        **book.__dict__,
        "content_preview": content_preview
    }
    
    return book_dict


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update book metadata
    """
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Update fields
    update_data = book_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a book and its associated files
    """
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(book.file_path):
            os.remove(book.file_path)
    except Exception as e:
        # Log error but continue with database deletion
        pass
    
    # Delete from database
    db.delete(book)
    db.commit()
    
    return None