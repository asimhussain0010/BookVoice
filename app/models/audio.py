"""
Audio File Model
Database model for generated audio files
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AudioStatus(str, enum.Enum):
    """Audio generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioFile(Base):
    """Generated audio file model"""
    
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    
    # Audio file information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    duration = Column(Float, nullable=True)  # in seconds
    format = Column(String, default="mp3")
    
    # Processing information
    status = Column(Enum(AudioStatus), default=AudioStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(String, nullable=True)
    
    # TTS settings used
    voice = Column(String, default="en-US-Standard-A")
    language = Column(String, default="en")
    speed = Column(Float, default=1.0)
    
    # Celery task tracking
    task_id = Column(String, nullable=True, unique=True)
    
    # Flags
    is_downloaded = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="audio_files")
    book = relationship("Book", back_populates="audio_files")
    
    def __repr__(self):
        return f"<AudioFile(id={self.id}, book_id={self.book_id}, status={self.status})>"