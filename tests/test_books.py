"""
Book Management Tests
Unit tests for book upload and management functionality
"""

import pytest
import os
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.book import Book, BookStatus
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
    
    # Create user
    user = User(
        email="booktest@example.com",
        username="booktester",
        hashed_password=hash_password("Test1234"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Login to get token
    response = client.post("/api/v1/auth/login", json={
        "email": "booktest@example.com",
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
    """Create a test book"""
    db = TestingSessionLocal()
    
    book = Book(
        user_id=test_user["user"].id,
        title="Test Book",
        author="Test Author",
        filename="test.txt",
        file_path="/tmp/test.txt",
        file_size=1024,
        file_type="txt",
        content="This is a test book content.",
        word_count=6,
        character_count=30,
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


class TestBookUpload:
    """Test book upload functionality"""
    
    def test_upload_txt_file(self, test_user):
        """Test uploading a TXT file"""
        # Create a test file
        file_content = b"This is a test book.\n\nChapter 1: Introduction\n\nThis is the introduction."
        file = io.BytesIO(file_content)
        
        response = client.post(
            "/api/v1/books/upload",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            files={"file": ("test.txt", file, "text/plain")},
            data={
                "title": "Test Book",
                "author": "Test Author",
                "language": "en"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Book"
        assert data["author"] == "Test Author"
        assert data["file_type"] == "txt"
        assert data["status"] in ["processing", "ready"]
    
    def test_upload_without_auth(self):
        """Test upload without authentication"""
        file = io.BytesIO(b"test content")
        
        response = client.post(
            "/api/v1/books/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={"title": "Test Book"}
        )
        
        assert response.status_code == 403
    
    def test_upload_invalid_file_type(self, test_user):
        """Test uploading an invalid file type"""
        file = io.BytesIO(b"test content")
        
        response = client.post(
            "/api/v1/books/upload",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            files={"file": ("test.xyz", file, "application/octet-stream")},
            data={"title": "Test Book"}
        )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"].lower()
    
    def test_upload_empty_file(self, test_user):
        """Test uploading an empty file"""
        file = io.BytesIO(b"")
        
        response = client.post(
            "/api/v1/books/upload",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            files={"file": ("empty.txt", file, "text/plain")},
            data={"title": "Empty Book"}
        )
        
        # Should fail during text extraction
        assert response.status_code in [400, 500]


class TestBookRetrieval:
    """Test book retrieval functionality"""
    
    def test_get_all_books(self, test_user, test_book):
        """Test getting all books for a user"""
        response = client.get(
            "/api/v1/books/",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) > 0
    
    def test_get_books_pagination(self, test_user, test_book):
        """Test book list pagination"""
        response = client.get(
            "/api/v1/books/?page=1&page_size=5",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_get_specific_book(self, test_user, test_book):
        """Test getting a specific book"""
        response = client.get(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_book.id
        assert data["title"] == test_book.title
    
    def test_get_nonexistent_book(self, test_user):
        """Test getting a book that doesn't exist"""
        response = client.get(
            "/api/v1/books/99999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 404
    
    def test_get_other_users_book(self, test_book):
        """Test accessing another user's book"""
        # Create another user
        db = TestingSessionLocal()
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=hash_password("Test1234"),
            is_active=True
        )
        db.add(other_user)
        db.commit()
        
        # Login as other user
        response = client.post("/api/v1/auth/login", json={
            "email": "other@example.com",
            "password": "Test1234"
        })
        other_token = response.json()["access_token"]
        
        # Try to access first user's book
        response = client.get(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 404
        
        # Cleanup
        db.delete(other_user)
        db.commit()
        db.close()


class TestBookUpdate:
    """Test book update functionality"""
    
    def test_update_book_title(self, test_user, test_book):
        """Test updating book title"""
        response = client.put(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"title": "Updated Title"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_update_book_author(self, test_user, test_book):
        """Test updating book author"""
        response = client.put(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"author": "New Author"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["author"] == "New Author"
    
    def test_update_multiple_fields(self, test_user, test_book):
        """Test updating multiple book fields"""
        response = client.put(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={
                "title": "New Title",
                "author": "New Author",
                "language": "es"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["language"] == "es"
    
    def test_update_nonexistent_book(self, test_user):
        """Test updating a book that doesn't exist"""
        response = client.put(
            "/api/v1/books/99999",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            json={"title": "New Title"}
        )
        
        assert response.status_code == 404


class TestBookDeletion:
    """Test book deletion functionality"""
    
    def test_delete_book(self, test_user, test_book):
        """Test deleting a book"""
        response = client.delete(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 204
        
        # Verify book is deleted
        response = client.get(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert response.status_code == 404
    
    def test_delete_nonexistent_book(self, test_user):
        """Test deleting a book that doesn't exist"""
        response = client.delete(
            "/api/v1/books/99999",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 404
    
    def test_delete_without_auth(self, test_book):
        """Test deleting without authentication"""
        response = client.delete(f"/api/v1/books/{test_book.id}")
        assert response.status_code == 403


class TestBookContent:
    """Test book content processing"""
    
    def test_book_has_content(self, test_user, test_book):
        """Test that processed book has content"""
        response = client.get(
            f"/api/v1/books/{test_book.id}",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "ready":
            assert "content_preview" in data
    
    def test_word_count_accuracy(self, test_user):
        """Test that word count is calculated correctly"""
        file_content = b"One two three four five"
        file = io.BytesIO(file_content)
        
        response = client.post(
            "/api/v1/books/upload",
            headers={"Authorization": f"Bearer {test_user['token']}"},
            files={"file": ("test.txt", file, "text/plain")},
            data={"title": "Word Count Test"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Word count should be 5 (after processing)
        if data["status"] == "ready":
            assert data["word_count"] == 5


# Cleanup after all tests
def teardown_module():
    """Clean up test database"""
    if os.path.exists("./test.db"):
        os.remove("./test.db")