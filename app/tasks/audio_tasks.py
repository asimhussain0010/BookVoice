"""
Celery Background Tasks
Handles long-running audio generation tasks
"""

import os
from datetime import datetime
from celery import Celery
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models.audio import AudioFile, AudioStatus
from app.models.book import Book
from app.services.tts_service import TTSService

# Initialize Celery
celery_app = Celery(
    "bookvoice",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
)


@celery_app.task(bind=True, name="generate_audio")
def generate_audio_task(self, audio_id: int, book_id: int, language: str = "en"):
    """
    Background task to generate audio from book text
    
    Args:
        self: Celery task instance (for progress updates)
        audio_id: AudioFile database ID
        book_id: Book database ID
        language: Language code for TTS
    """
    db = SessionLocal()
    
    try:
        # Get audio file and book records
        audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
        book = db.query(Book).filter(Book.id == book_id).first()
        
        if not audio_file or not book:
            raise Exception("Audio file or book not found")
        
        # Update status to processing
        audio_file.status = AudioStatus.PROCESSING
        audio_file.progress = 0
        db.commit()
        
        # Get book content
        if not book.content:
            raise Exception("Book has no content to convert")
        
        # Initialize TTS service
        tts_service = TTSService()
        
        # Define progress callback
        def update_progress(progress: int):
            audio_file.progress = progress
            db.commit()
            
            # Update Celery task state
            self.update_state(
                state='PROGRESS',
                meta={'current': progress, 'total': 100}
            )
        
        # Generate audio
        output_path = os.path.join(
            settings.AUDIO_DIR,
            f"audio_{audio_id}_{datetime.utcnow().timestamp()}.mp3"
        )
        
        # Ensure audio directory exists
        os.makedirs(settings.AUDIO_DIR, exist_ok=True)
        
        result = tts_service.convert_to_audio(
            text=book.content,
            output_path=output_path,
            language=language,
            progress_callback=update_progress
        )
        
        # Update audio file record
        audio_file.status = AudioStatus.COMPLETED
        audio_file.progress = 100
        audio_file.file_path = result['file_path']
        audio_file.file_size = result['file_size']
        audio_file.duration = result['duration']
        audio_file.completed_at = datetime.utcnow()
        
        db.commit()
        
        return {
            'status': 'completed',
            'audio_id': audio_id,
            'file_path': result['file_path'],
            'duration': result['duration']
        }
        
    except Exception as e:
        # Update status to failed
        if audio_file:
            audio_file.status = AudioStatus.FAILED
            audio_file.error_message = str(e)
            db.commit()
        
        raise Exception(f"Audio generation failed: {str(e)}")
        
    finally:
        db.close()


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """
    Periodic task to clean up old temporary files
    Run daily via Celery Beat
    """
    db = SessionLocal()
    
    try:
        # This would implement logic to remove old files
        # based on retention policy
        pass
        
    finally:
        db.close()