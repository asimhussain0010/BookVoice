"""
Authentication Tests
Unit tests for authentication functionality
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.core.security import hash_password

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
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
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("Test1234"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


class TestRegistration:
    """Test user registration"""
    
    def test_register_success(self):
        """Test successful registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "NewPass123",
            "password_confirm": "NewPass123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
    
    def test_register_duplicate_email(self, test_user):
        """Test registration with duplicate email"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "username": "anotheruser",
            "password": "Test1234",
            "password_confirm": "Test1234"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "weak",
            "password_confirm": "weak"
        })
        assert response.status_code == 422
    
    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "Test1234",
            "password_confirm": "Different123"
        })
        assert response.status_code == 422


class TestLogin:
    """Test user login"""
    
    def test_login_success(self, test_user):
        """Test successful login"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_wrong_password(self, test_user):
        """Test login with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Test1234"
        })
        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh"""
    
    def test_refresh_token_success(self, test_user):
        """Test successful token refresh"""
        # First login
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token"""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401


class TestProtectedRoutes:
    """Test protected routes"""
    
    def test_access_protected_without_token(self):
        """Test accessing protected route without token"""
        response = client.get("/api/v1/books/")
        assert response.status_code == 403
    
    def test_access_protected_with_token(self, test_user):
        """Test accessing protected route with valid token"""
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]
        
        # Access protected route
        response = client.get(
            "/api/v1/books/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200


# Additional test files would include:
# - tests/test_books.py - Book upload and management tests
# - tests/test_audio.py - Audio generation tests
# - tests/test_services.py - Service layer tests
# - tests/test_utils.py - Utility function tests