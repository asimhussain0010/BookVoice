"""
Book Model
Database model for uploaded books/ebooks
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class BookStatus(str, enum.Enum):
    """Book processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Book(Base):
    """Book/eBook model"""
    
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False)
    author = Column(String, nullable=True)
    language = Column(String, default="en")
    
    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String, nullable=False)  # pdf, epub, txt, docx
    
    # Extracted text
    content = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(BookStatus), default=BookStatus.UPLOADED)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="books")
    audio_files = relationship("AudioFile", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, status={self.status})>"