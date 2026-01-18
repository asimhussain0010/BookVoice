"""
Storage Service
Handles file storage operations (local filesystem, S3, etc.)
"""

import os
import shutil
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
from app.config import settings
from app.utils.helpers import ensure_directory_exists, generate_unique_filename
from app.utils.constants import UPLOAD_DIRECTORY, AUDIO_DIRECTORY


class StorageService:
    """
    File storage service
    Can be extended to support cloud storage (S3, Azure, GCP)
    """
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.audio_dir = settings.AUDIO_DIR
        
        # Ensure directories exist
        ensure_directory_exists(self.upload_dir)
        ensure_directory_exists(self.audio_dir)
    
    def save_upload(self, file: BinaryIO, filename: str, user_id: int) -> dict:
        """
        Save uploaded file
        
        Args:
            file: File-like object
            filename: Original filename
            user_id: User ID for organizing files
            
        Returns:
            Dictionary with file information
        """
        # Generate unique filename
        unique_filename = generate_unique_filename(filename, prefix=str(user_id))
        
        # Create user directory
        user_dir = os.path.join(self.upload_dir, str(user_id))
        ensure_directory_exists(user_dir)
        
        # Full file path
        file_path = os.path.join(user_dir, unique_filename)
        
        # Save file
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            'filename': unique_filename,
            'file_path': file_path,
            'file_size': file_size,
            'original_filename': filename
        }
    
    def save_audio(self, audio_path: str, filename: str, user_id: int) -> dict:
        """
        Save generated audio file
        
        Args:
            audio_path: Path to temporary audio file
            filename: Desired filename
            user_id: User ID
            
        Returns:
            Dictionary with file information
        """
        # Generate unique filename
        unique_filename = generate_unique_filename(filename, prefix=str(user_id))
        
        # Create user directory
        user_dir = os.path.join(self.audio_dir, str(user_id))
        ensure_directory_exists(user_dir)
        
        # Full file path
        file_path = os.path.join(user_dir, unique_filename)
        
        # Copy file
        shutil.copy2(audio_path, file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            'filename': unique_filename,
            'file_path': file_path,
            'file_size': file_size
        }
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted successfully
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists
        """
        return os.path.exists(file_path)
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get file size
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def clean_old_files(self, days: int = 30) -> int:
        """
        Clean up old files
        
        Args:
            days: Delete files older than this many days
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days * 86400)
        
        for directory in [self.upload_dir, self.audio_dir]:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_date:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except:
                            pass
        
        return deleted_count
    
    def get_storage_usage(self, user_id: Optional[int] = None) -> dict:
        """
        Get storage usage statistics
        
        Args:
            user_id: Optional user ID to get specific user's usage
            
        Returns:
            Dictionary with storage statistics
        """
        total_size = 0
        file_count = 0
        
        if user_id:
            # User-specific directories
            user_upload_dir = os.path.join(self.upload_dir, str(user_id))
            user_audio_dir = os.path.join(self.audio_dir, str(user_id))
            directories = [user_upload_dir, user_audio_dir]
        else:
            # All directories
            directories = [self.upload_dir, self.audio_dir]
        
        for directory in directories:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except:
                            pass
        
        return {
            'total_size': total_size,
            'file_count': file_count,
            'total_size_mb': total_size / (1024 * 1024)
        }


class S3StorageService(StorageService):
    """
    S3-compatible storage service (AWS S3, MinIO, etc.)
    Extends base StorageService for cloud storage
    """
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        super().__init__()
        self.bucket_name = bucket_name
        self.region = region
        
        # Initialize S3 client (requires boto3)
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        except ImportError:
            print("boto3 not installed. S3 storage not available.")
            self.s3_client = None
    
    def save_upload(self, file: BinaryIO, filename: str, user_id: int) -> dict:
        """Save file to S3"""
        if not self.s3_client:
            return super().save_upload(file, filename, user_id)
        
        # Generate S3 key
        unique_filename = generate_unique_filename(filename, prefix=str(user_id))
        s3_key = f"uploads/{user_id}/{unique_filename}"
        
        # Upload to S3
        try:
            self.s3_client.upload_fileobj(file, self.bucket_name, s3_key)
            
            # Generate presigned URL (optional)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600
            )
            
            return {
                'filename': unique_filename,
                'file_path': s3_key,
                'file_size': 0,  # Would need to calculate
                'url': url
            }
        except Exception as e:
            print(f"S3 upload error: {e}")
            # Fallback to local storage
            return super().save_upload(file, filename, user_id)