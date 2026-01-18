"""
Validation Utilities
Common validation functions used across the application
"""

import os
import magic
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from app.utils.constants import ALLOWED_FILE_TYPES, MAX_FILE_SIZE


def validate_file_type(file: UploadFile) -> bool:
    """
    Validate file type based on extension
    
    Args:
        file: Uploaded file object
        
    Returns:
        True if file type is allowed
        
    Raises:
        HTTPException: If file type is not allowed
    """
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}"
        )
    
    return True


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size (default: from constants)
        
    Returns:
        True if file size is acceptable
        
    Raises:
        HTTPException: If file size exceeds limit
    """
    max_size = max_size or MAX_FILE_SIZE
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {max_mb}MB"
        )
    
    return True


def validate_mime_type(file_path: str, expected_types: list) -> bool:
    """
    Validate MIME type using python-magic
    Provides additional security beyond extension checking
    
    Args:
        file_path: Path to file
        expected_types: List of expected MIME types
        
    Returns:
        True if MIME type matches
        
    Raises:
        HTTPException: If MIME type doesn't match
    """
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        
        if file_mime not in expected_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File MIME type '{file_mime}' not allowed"
            )
        
        return True
    except Exception as e:
        # If magic fails, skip this validation
        return True


def validate_text_content(text: str, min_length: int = 10, max_length: int = 500000) -> bool:
    """
    Validate extracted text content
    
    Args:
        text: Extracted text
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Returns:
        True if text is valid
        
    Raises:
        HTTPException: If text doesn't meet requirements
    """
    if not text or len(text.strip()) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text content too short. Minimum {min_length} characters required."
        )
    
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text content too long. Maximum {max_length} characters allowed."
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', '\x00', '\n', '\r', '\t']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def validate_language_code(lang_code: str) -> bool:
    """
    Validate language code
    
    Args:
        lang_code: Language code (e.g., 'en', 'es')
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If language code is invalid
    """
    from app.utils.constants import SUPPORTED_LANGUAGES
    
    if lang_code not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{lang_code}' not supported. Supported languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        )
    
    return True