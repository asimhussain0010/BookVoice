"""
Book Schemas
Pydantic models for book request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.book import BookStatus


class BookBase(BaseModel):
    """Base book schema"""
    title: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    language: str = Field(default="en", max_length=10)


class BookCreate(BookBase):
    """Schema for creating a book (after upload)"""
    pass


class BookUpdate(BaseModel):
    """Schema for updating book metadata"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)


class BookResponse(BookBase):
    """Schema for book response"""
    id: int
    user_id: int
    filename: str
    file_size: int
    file_type: str
    word_count: int
    character_count: int
    status: BookStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BookDetail(BookResponse):
    """Schema for detailed book response with content preview"""
    content_preview: Optional[str] = None


class BookListResponse(BaseModel):
    """Schema for paginated book list"""
    items: list[BookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int