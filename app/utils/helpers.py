"""
Helper Utilities
Common helper functions used across the application
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union


def format_bytes(bytes: int) -> str:
    """
    Convert bytes to human-readable format
    
    Args:
        bytes: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if bytes == 0:
        return "0 Bytes"
    
    sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while bytes >= 1024 and i < len(sizes) - 1:
        bytes /= 1024
        i += 1
    
    return f"{bytes:.2f} {sizes[i]}"


def format_duration(seconds: float) -> str:
    """
    Convert seconds to human-readable duration
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1h 30m 45s")
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def generate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of a file
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hexadecimal hash string
    """
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: File name
        
    Returns:
        File extension (e.g., '.pdf')
    """
    return os.path.splitext(filename)[1].lower()


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate a unique filename using timestamp
    
    Args:
        original_filename: Original file name
        prefix: Optional prefix
        
    Returns:
        Unique filename
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    name, ext = os.path.splitext(original_filename)
    
    if prefix:
        return f"{prefix}_{timestamp}{ext}"
    return f"{timestamp}_{name}{ext}"


def calculate_reading_time(word_count: int, words_per_minute: int = 200) -> int:
    """
    Calculate estimated reading time in minutes
    
    Args:
        word_count: Number of words
        words_per_minute: Average reading speed
        
    Returns:
        Estimated reading time in minutes
    """
    if word_count <= 0:
        return 0
    
    return max(1, int(word_count / words_per_minute))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    Parse time string to timedelta
    
    Args:
        time_str: Time string (e.g., "1h 30m", "45s")
        
    Returns:
        timedelta object or None
    """
    try:
        total_seconds = 0
        parts = time_str.lower().split()
        
        for part in parts:
            if part.endswith('h'):
                total_seconds += int(part[:-1]) * 3600
            elif part.endswith('m'):
                total_seconds += int(part[:-1]) * 60
            elif part.endswith('s'):
                total_seconds += int(part[:-1])
        
        return timedelta(seconds=total_seconds)
    except:
        return None


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def clean_text(text: str) -> str:
    """
    Clean text by removing excessive whitespace and special characters
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    import re
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()


def create_slug(text: str) -> str:
    """
    Create URL-friendly slug from text
    
    Args:
        text: Text to convert
        
    Returns:
        Slug
    """
    import re
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Trim hyphens from ends
    slug = slug.strip('-')
    
    return slug


def paginate(query, page: int, page_size: int):
    """
    Paginate SQLAlchemy query
    
    Args:
        query: SQLAlchemy query
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Tuple of (items, total, total_pages)
    """
    total = query.count()
    
    # Calculate pagination
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return items, total, total_pages