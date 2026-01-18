"""
Book Service
Business logic for book processing
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.book import Book, BookStatus
from app.services.text_extractor import TextExtractor
from app.services.storage_service import StorageService


class BookService:
    """Book processing business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.text_extractor = TextExtractor()
        self.storage_service = StorageService()
    
    def create_book(
        self,
        user_id: int,
        title: str,
        file_path: str,
        filename: str,
        file_size: int,
        file_type: str,
        author: Optional[str] = None,
        language: str = "en"
    ) -> Book:
        """
        Create a new book entry
        
        Args:
            user_id: Owner user ID
            title: Book title
            file_path: Path to uploaded file
            filename: Original filename
            file_size: File size in bytes
            file_type: File type (pdf, epub, etc.)
            author: Book author (optional)
            language: Book language
            
        Returns:
            Created book
        """
        book = Book(
            user_id=user_id,
            title=title,
            author=author,
            language=language,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type.replace('.', ''),
            status=BookStatus.UPLOADED
        )
        
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        
        return book
    
    def process_book(self, book_id: int) -> Book:
        """
        Process book - extract text content
        
        Args:
            book_id: Book ID
            
        Returns:
            Updated book
        """
        book = self.db.query(Book).filter(Book.id == book_id).first()
        
        if not book:
            raise ValueError("Book not found")
        
        try:
            # Update status to processing
            book.status = BookStatus.PROCESSING
            self.db.commit()
            
            # Extract text
            text, word_count, char_count = self.text_extractor.extract(
                book.file_path,
                book.file_type
            )
            
            # Update book with extracted content
            book.content = text
            book.word_count = word_count
            book.character_count = char_count
            book.status = BookStatus.READY
            book.processed_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(book)
            
            return book
            
        except Exception as e:
            # Update status to error
            book.status = BookStatus.ERROR
            book.error_message = str(e)
            self.db.commit()
            raise
    
    def get_user_books(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> tuple[List[Book], int]:
        """
        Get user's books with pagination
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (books, total_count)
        """
        query = self.db.query(Book).filter(Book.user_id == user_id)
        total = query.count()
        books = query.order_by(Book.created_at.desc()).offset(skip).limit(limit).all()
        
        return books, total
    
    def get_book(self, book_id: int, user_id: int) -> Optional[Book]:
        """Get book by ID (with user verification)"""
        return self.db.query(Book).filter(
            Book.id == book_id,
            Book.user_id == user_id
        ).first()
    
    def update_book(
        self,
        book_id: int,
        user_id: int,
        title: Optional[str] = None,
        author: Optional[str] = None,
        language: Optional[str] = None
    ) -> Book:
        """Update book metadata"""
        book = self.get_book(book_id, user_id)
        
        if not book:
            raise ValueError("Book not found")
        
        if title:
            book.title = title
        if author:
            book.author = author
        if language:
            book.language = language
        
        self.db.commit()
        self.db.refresh(book)
        
        return book
    
    def delete_book(self, book_id: int, user_id: int) -> bool:
        """
        Delete book and associated files
        
        Args:
            book_id: Book ID
            user_id: User ID
            
        Returns:
            True if deleted successfully
        """
        book = self.get_book(book_id, user_id)
        
        if not book:
            return False
        
        # Delete file from storage
        self.storage_service.delete_file(book.file_path)
        
        # Delete from database
        self.db.delete(book)
        self.db.commit()
        
        return True
    
    def get_book_preview(self, book_id: int, user_id: int, length: int = 500) -> str:
        """Get preview of book content"""
        book = self.get_book(book_id, user_id)
        
        if not book or not book.content:
            return ""
        
        return self.text_extractor.preview_text(book.content, length)