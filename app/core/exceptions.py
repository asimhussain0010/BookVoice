# app/core/exceptions.py
"""
Custom application exceptions
"""

from fastapi import HTTPException, status


class BookVoiceException(Exception):
    """Base exception for BookVoice application"""
    pass


class AuthenticationError(BookVoiceException):
    """Authentication related errors"""
    pass


class BookProcessingError(BookVoiceException):
    """Book processing errors"""
    pass


class AudioGenerationError(BookVoiceException):
    """Audio generation errors"""
    pass


class ValidationError(BookVoiceException):
    """Data validation errors"""
    pass


class StorageError(BookVoiceException):
    """File storage errors"""
    pass
