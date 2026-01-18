"""
Audio Generation Tests
Unit tests for audio generation and management functionality
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.book import Book, BookStatus
from app.models.audio import AudioFile, AudioStatus
from app.core.security import hash_password

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user and return with token"""
    db = TestingSessionLocal()
    
    user = User(
        email="audiotest@example.com",
        username="audiotester",
        hashed_password=hash_password("Test1234"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Login to get token
    response = client.post("/api/v1/auth/login", json={
        "email": "audiotest@example.com",
        "password": "Test1234"
    })
    token = response.json()["access_token"]
    
    yield {"user": user, "token": token}
    
    # Cleanup
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def test_book(test_user):
    """Create a test book ready for audio generation"""
    db = TestingSessionLocal()
    
    book = Book(
        user_id=test_user["user"].id,
        title="Audio Test Book",
        author="Test Author",
        filename="audiotest.txt",
        file_path="/tmp/audiotest.txt",
        file_size=2048,
        file_type="txt",
        content="This is a test book for audio generation. It has multiple sentences. This helps test the TTS functionality.",
        word_count=20,
        character_count=100,
        status=BookStatus.READY
    )
    
    db.add(book)
    db.commit()
    db.refresh(book)
    
    yield book
    
    # Cleanup
    db.delete(book)
    db.commit()
    db.close()


@pytest.fixture
def test_audio(test_user, test_book):
    """Create a test audio file"""
    db = TestingSessionLocal()
    
    audio = AudioFile(
        user_id=test_user["user"].id,
        book_id=test_book.id,
        filename="test_audio.mp3",
        file_path="/tmp/test_audio.mp3",
        status=AudioStatus.PENDING,
        language="en",
        voice="en-US-Standard-A",
        speed=1.0
    )
    
    db.add(audio)
    db.commit()
    db.refresh(audio)
    
    yield audio
    
    # Cleanup
    db.delete(audio)
    db.commit()
    db.close()


class TestAudioGeneration:
    """Test audio generation functionality"""
    
    def test_generate_audio_request(self, test_user, test_book):
        """Test creating an audio generation request"""
        response = client.post(
            "/api/v1/audio/generate",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "book_id": test_book.id,
                "language": "en",
                "voice": "en-US-Standard-A",
                "speed": 1.0
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["book_id"] == test_book.id
        assert data["status"] in ["pending", "processing"]
        assert "task_id" in data
    
    def test_generate_audio_without_auth(self, test_book):
        """Test generating audio without authentication"""
        response = client.post(
            "/api/v1/audio/generate",
            json={"book_id": test_book.id}
        )
        
        assert response.status_code == 403
    
    def test_generate_audio_nonexistent_book(self, test_user):
        """Test generating audio for non-existent book"""
        response = client.post(
            "/api/v1/audio/generate",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "book_id": 99999,
                "language": "en"
            }
        )
        
        assert response.status_code == 404
    
    def test_generate_audio_unprocessed_book(self, test_user):
        """Test generating audio for unprocessed book"""
        db = TestingSessionLocal()
        
        # Create book without content
        unprocessed_book = Book(
            user_id=test_user["user"].id,
            title="Unprocessed Book",
            filename="unprocessed.txt",
            file_path="/tmp/unprocessed.txt",
            file_size=1024,
            file_type="txt",
            status=BookStatus.UPLOADED
        )
        db.add(unprocessed_book)
        db.commit()
        db.refresh(unprocessed_book)
        
        response = client.post(
            "/api/v1/audio/generate",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "book_id": unprocessed_book.id,
                "language": "en"
            }
        )
        
        assert response.status_code == 400
        
        # Cleanup
        db.delete(unprocessed_book)
        db.commit()
        db.close()
    
    def test_generate_audio_custom_settings(self, test_user, test_book):
        """Test generating audio with custom settings"""
        response = client.post(
            "/api/v1/audio/generate",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "book_id": test_book.id,
                "language": "en",
                "voice": "en-GB-Standard-A",
                "speed": 1.5
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["language"] == "en"
        assert data["voice"] == "en-GB-Standard-A"
        assert data["speed"] == 1.5


class TestAudioRetrieval:
    """Test audio file retrieval"""
    
    def test_get_all_audio_files(self, test_user, test_audio):
        """Test getting all audio files for a user"""
        response = client.get(
            "/api/v1/audio/",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
    
    def test_get_audio_pagination(self, test_user, test_audio):
        """Test audio list pagination"""
        response = client.get(
            "/api/v1/audio/?page=1&page_size=5",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_get_specific_audio(self, test_user, test_audio):
        """Test getting a specific audio file"""
        response = client.get(
            f"/api/v1/audio/{test_audio.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_audio.id
        assert data["book_id"] == test_audio.book_id
    
    def test_get_nonexistent_audio(self, test_user):
        """Test getting audio that doesn't exist"""
        response = client.get(
            "/api/v1/audio/99999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 404


class TestAudioStatus:
    """Test audio generation status tracking"""
    
    def test_get_audio_status(self, test_user, test_audio):
        """Test getting audio generation status"""
        response = client.get(
            f"/api/v1/audio/{test_audio.id}/status",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data
        assert data["id"] == test_audio.id
    
    def test_status_shows_progress(self, test_user, test_audio):
        """Test that status includes progress information"""
        response = client.get(
            f"/api/v1/audio/{test_audio.id}/status",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "progress" in data
        assert 0 <= data["progress"] <= 100
    
    def test_status_shows_errors(self, test_user):
        """Test that status shows error messages"""
        db = TestingSessionLocal()
        
        # Create audio with error
        failed_audio = AudioFile(
            user_id=test_user["user"].id,
            book_id=1,
            filename="failed.mp3",
            file_path="/tmp/failed.mp3",
            status=AudioStatus.FAILED,
            error_message="Test error message"
        )
        db.add(failed_audio)
        db.commit()
        db.refresh(failed_audio)
        
        response = client.get(
            f"/api/v1/audio/{failed_audio.id}/status",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "Test error message"
        
        # Cleanup
        db.delete(failed_audio)
        db.commit()
        db.close()


class TestAudioDownload:
    """Test audio file download"""
    
    def test_download_completed_audio(self, test_user):
        """Test downloading completed audio file"""
        db = TestingSessionLocal()
        
        # Create completed audio (we'll mock the file)
        completed_audio = AudioFile(
            user_id=test_user["user"].id,
            book_id=1,
            filename="completed.mp3",
            file_path="/tmp/completed.mp3",
            file_size=1024000,
            duration=120.5,
            status=AudioStatus.COMPLETED
        )
        db.add(completed_audio)
        db.commit()
        db.refresh(completed_audio)
        
        # Create dummy file
        with open("/tmp/completed.mp3", "wb") as f:
            f.write(b"fake audio data")
        
        response = client.get(
            f"/api/v1/audio/{completed_audio.id}/download",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        # Should return file or redirect
        assert response.status_code in [200, 302]
        
        # Cleanup
        if os.path.exists("/tmp/completed.mp3"):
            os.remove("/tmp/completed.mp3")
        db.delete(completed_audio)
        db.commit()
        db.close()
    
    def test_download_pending_audio(self, test_user, test_audio):
        """Test downloading audio that's not ready"""
        response = client.get(
            f"/api/v1/audio/{test_audio.id}/download",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 400
    
    def test_download_without_auth(self, test_audio):
        """Test downloading without authentication"""
        response = client.get(f"/api/v1/audio/{test_audio.id}/download")
        assert response.status_code == 403


class TestAudioDeletion:
    """Test audio file deletion"""
    
    def test_delete_audio(self, test_user, test_audio):
        """Test deleting an audio file"""
        response = client.delete(
            f"/api/v1/audio/{test_audio.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 204
        
        # Verify audio is deleted
        response = client.get(
            f"/api/v1/audio/{test_audio.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert response.status_code == 404
    
    def test_delete_nonexistent_audio(self, test_user):
        """Test deleting audio that doesn't exist"""
        response = client.delete(
            "/api/v1/audio/99999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_without_auth(self, test_audio):
        """Test deleting without authentication"""
        response = client.delete(f"/api/v1/audio/{test_audio.id}")
        assert response.status_code == 403


class TestAudioMetadata:
    """Test audio file metadata"""
    
    def test_audio_has_correct_metadata(self, test_user, test_audio):
        """Test that audio file has correct metadata"""
        response = client.get(
            f"/api/v1/audio/{test_audio.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "language" in data
        assert "voice" in data
        assert "speed" in data
        assert "format" in data
        assert data["format"] == "mp3"
    
    def test_audio_tracks_downloads(self, test_user):
        """Test that downloads are tracked"""
        db = TestingSessionLocal()
        
        completed_audio = AudioFile(
            user_id=test_user["user"].id,
            book_id=1,
            filename="track.mp3",
            file_path="/tmp/track.mp3",
            status=AudioStatus.COMPLETED,
            download_count=0
        )
        db.add(completed_audio)
        db.commit()
        db.refresh(completed_audio)
        
        # Get initial download count
        response = client.get(
            f"/api/v1/audio/{completed_audio.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        initial_count = response.json()["download_count"]
        
        # This would increase after actual download
        assert initial_count == 0
        
        # Cleanup
        db.delete(completed_audio)
        db.commit()
        db.close()


# Cleanup after all tests
def teardown_module():
    """Clean up test database and files"""
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    
    # Clean up any test files
    test_files = [
        "/tmp/audiotest.txt",
        "/tmp/test_audio.mp3",
        "/tmp/completed.mp3",
        "/tmp/track.mp3"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            os.remove(file_path)