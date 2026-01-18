# app/api/__init__.py
"""
API routes
"""

from app.api import auth, books, audio

__all__ = ["auth", "books", "audio"]