"""
Celery Application Configuration
Configures Celery for background task processing
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery application
celery_app = Celery(
    "bookvoice",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.audio_tasks']
)

# Celery Configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time zone
    timezone='UTC',
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Task execution
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task retry
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Broker
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)

# Periodic tasks (optional - requires celery beat)
celery_app.conf.beat_schedule = {
    # Clean up old files daily at 2 AM
    'cleanup-old-files': {
        'task': 'app.tasks.audio_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),
        'args': (30,)  # Delete files older than 30 days
    },
}

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    'app.tasks.audio_tasks.generate_audio_task': {
        'queue': 'audio_generation',
        'routing_key': 'audio.generate',
    },
    'app.tasks.audio_tasks.cleanup_old_files': {
        'queue': 'maintenance',
        'routing_key': 'maintenance.cleanup',
    },
}

# Import tasks to register them
from app.tasks import audio_tasks

if __name__ == '__main__':
    celery_app.start()