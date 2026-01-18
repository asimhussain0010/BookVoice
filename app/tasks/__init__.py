# app/tasks/__init__.py
"""
Background tasks
"""

from app.tasks.celery_app import celery_app
from app.tasks.audio_tasks import generate_audio_task

__all__ = [
    "celery_app",
    "generate_audio_task"
]