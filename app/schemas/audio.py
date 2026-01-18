"""
Audio Schemas
Pydantic models for audio request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.audio import AudioStatus


class AudioCreate(BaseModel):
    """Schema for creating audio generation request"""
    book_id: int
    language: Optional[str] = Field(None, max_length=10)
    voice: str = Field(default="en-US-Standard-A", max_length=50)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class AudioResponse(BaseModel):
    """Schema for audio file response"""
    id: int
    user_id: int
    book_id: int
    filename: str
    file_size: Optional[int] = None
    duration: Optional[float] = None
    format: str
    status: AudioStatus
    progress: int
    error_message: Optional[str] = None
    voice: str
    language: str
    speed: float
    task_id: Optional[str] = None
    is_downloaded: bool
    download_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AudioListResponse(BaseModel):
    """Schema for paginated audio list"""
    items: list[AudioResponse]
    total: int
    page: int
    page_size: int
    total_pages: int