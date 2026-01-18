# BookVoice - Production-Grade eBook to Audio Platform

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [API Documentation](#api-documentation)
9. [Deployment](#deployment)
10. [Security Considerations](#security-considerations)
11. [Scaling](#scaling)
12. [Troubleshooting](#troubleshooting)

---

## Overview

BookVoice is an enterprise-ready SaaS application that converts eBooks into high-quality audio using advanced Text-to-Speech technology. Built with Python, FastAPI, and modern web technologies.

### Technology Stack
- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **TTS Engine**: gTTS (Google TTS) / pyttsx3
- **Frontend**: HTML5, Tailwind CSS, Alpine.js
- **Container**: Docker, Docker Compose

---

## Features

### Core Functionality
- ✅ **User Authentication**: Secure JWT-based authentication with password hashing
- ✅ **Multi-Format Support**: PDF, EPUB, TXT, DOCX
- ✅ **Text Extraction**: Advanced text extraction from various formats
- ✅ **High-Quality TTS**: Multiple TTS engine support
- ✅ **Background Processing**: Celery-based asynchronous task processing
- ✅ **Real-Time Updates**: Live progress tracking
- ✅ **Audio Management**: Download, delete, and manage audio files
- ✅ **Responsive UI**: Modern, mobile-friendly interface

### Advanced Features
- Session management with Redis
- File upload with drag-and-drop
- Progress indicators for long-running tasks
- Comprehensive error handling
- API rate limiting (configurable)
- CORS support
- Database migrations with Alembic

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)           │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼─────┐      ┌──────▼────┐
│ FastAPI │      │  FastAPI  │
│ Instance│      │  Instance │
└───┬─────┘      └──────┬────┘
    │                   │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────────┐   ┌──────▼─────┐
│ PostgreSQL │   │   Redis    │
│  Database  │   │ Cache/Queue│
└────────────┘   └──────┬─────┘
                        │
                 ┌──────▼─────┐
                 │   Celery   │
                 │   Workers  │
                 └────────────┘
```

---

## Prerequisites

### Required Software
- Python 3.11 or higher
- PostgreSQL 13+ (or SQLite for development)
- Redis 6+
- FFmpeg (for audio processing)
- Git

### Optional
- Docker & Docker Compose (recommended)
- Nginx (for production)

---

## Installation

### Method 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/bookvoice.git
cd bookvoice

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Open http://localhost:8000
```

### Method 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/your-org/bookvoice.git
cd bookvoice

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install ffmpeg espeak postgresql redis-server

# Create database
sudo -u postgres psql
CREATE DATABASE bookvoice_db;
CREATE USER bookvoice_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bookvoice_db TO bookvoice_user;
\q

# Copy and configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Run database migrations
alembic upgrade head

# Start Redis
redis-server

# Start Celery worker (in separate terminal)
celery -A app.tasks.audio_tasks worker --loglevel=info

# Start application
uvicorn app.main:app --reload
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Security
SECRET_KEY=your-super-secret-key-minimum-32-characters
ALGORITHM=HS256

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/bookvoice_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Application
DEBUG=False
API_PREFIX=/api/v1
```

### Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Setup

```bash
# Create tables
python -c "from app.database import init_db; init_db()"

# Or use Alembic migrations
alembic upgrade head
```

---

## Running the Application

### Development Mode

```bash
# Terminal 1: Start main application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A app.tasks.audio_tasks worker --loglevel=info

# Terminal 3: Start Redis (if not running)
redis-server
```

### Production Mode

```bash
# Use gunicorn for production
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -

# Or use Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Access Points

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## API Documentation

### Authentication Endpoints

```
POST /api/v1/auth/register - Register new user
POST /api/v1/auth/login - Login user
POST /api/v1/auth/refresh - Refresh access token
POST /api/v1/auth/logout - Logout user
```

### Book Endpoints

```
POST /api/v1/books/upload - Upload book file
GET /api/v1/books/ - List user's books
GET /api/v1/books/{id} - Get book details
PUT /api/v1/books/{id} - Update book metadata
DELETE /api/v1/books/{id} - Delete book
```

### Audio Endpoints

```
POST /api/v1/audio/generate - Generate audio from book
GET /api/v1/audio/ - List user's audio files
GET /api/v1/audio/{id} - Get audio details
GET /api/v1/audio/{id}/status - Get generation status
GET /api/v1/audio/{id}/download - Download audio file
DELETE /api/v1/audio/{id} - Delete audio file
```

### Example API Usage

```python
import requests

# Register user
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123"
})

# Login
response = requests.post("http://localhost:8000/api/v1/auth/login", json={
    "email": "user@example.com",
    "password": "SecurePass123"
})
token = response.json()["access_token"]

# Upload book
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("book.pdf", "rb")}
data = {"title": "My Book", "author": "Author Name"}
response = requests.post(
    "http://localhost:8000/api/v1/books/upload",
    headers=headers,
    files=files,
    data=data
)
```

---

## Deployment

### Production Deployment with Docker

1. **Configure Production Environment**

```bash
# Create production .env
cp .env.example .env.production
nano .env.production

# Set production values
DEBUG=False
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@postgres:5432/bookvoice
```

2. **Deploy with Docker Compose**

```bash
# Build and start
docker-compose -f docker-compose.yml up -d --build

# Check logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale celery=3
```

### Deployment with Nginx

**nginx.conf:**

```nginx
upstream bookvoice {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name bookvoice.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://bookvoice;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/bookvoice/static;
        expires 30d;
    }
}
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d bookvoice.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Security Considerations

### Production Security Checklist

- [ ] Change default SECRET_KEY to strong random value
- [ ] Use HTTPS in production (SSL certificate)
- [ ] Enable database connection encryption
- [ ] Set DEBUG=False in production
- [ ] Configure CORS_ORIGINS properly
- [ ] Implement rate limiting
- [ ] Use strong database passwords
- [ ] Regular security updates
- [ ] Enable firewall rules
- [ ] Implement backup strategy
- [ ] Set up monitoring and logging
- [ ] Use environment variables for secrets
- [ ] Implement token blacklisting for logout

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Validated both client and server side

### JWT Token Security

- Access tokens expire in 60 minutes
- Refresh tokens expire in 7 days
- Tokens include user ID, email, username
- Secure algorithm (HS256)

---

## Scaling

### Horizontal Scaling

```bash
# Scale web application
docker-compose up -d --scale app=4

# Scale Celery workers
docker-compose up -d --scale celery=6

# Use load balancer (Nginx/HAProxy)
```

### Database Scaling

```yaml
# Read replicas
DATABASE_REPLICA_URL=postgresql://user:pass@replica:5432/bookvoice

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### Caching Strategy

```python
# Redis caching for frequently accessed data
# Session storage in Redis
# Task queue in Redis
```

### Performance Optimization

1. **Database Indexes**: Add indexes on frequently queried fields
2. **Query Optimization**: Use SQLAlchemy query optimization
3. **File Storage**: Use S3/MinIO for file storage
4. **CDN**: Use CDN for static files
5. **Compression**: Enable gzip compression
6. **Caching**: Implement Redis caching

---

## Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection
psql -U bookvoice_user -d bookvoice_db -h localhost
```

**Celery Not Processing Tasks**
```bash
# Check Redis connection
redis-cli ping

# Restart Celery worker
docker-compose restart celery

# Check worker logs
celery -A app.tasks.audio_tasks inspect active
```

**File Upload Fails**
```bash
# Check directory permissions
chmod 755 uploads/
chmod 755 app/static/audio/

# Check MAX_UPLOAD_SIZE in .env
```

**Audio Generation Fails**
```bash
# Check FFmpeg installation
ffmpeg -version

# Check espeak installation
espeak --version

# Check Celery logs
docker-compose logs celery
```

### Logging

```python
# Enable detailed logging
LOG_LEVEL=DEBUG

# View logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f app
```

---

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_auth.py
```

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

This project is licensed under the MIT License.

---

## Support

For support, email support@bookvoice.com or open an issue on GitHub.

---

## Roadmap

- [ ] Support for more TTS engines (AWS Polly, Azure TTS, ElevenLabs)
- [ ] Multi-voice support
- [ ] Chapter-based audio generation
- [ ] Audio editing capabilities
- [ ] Podcast-style formatting
- [ ] Social sharing features
- [ ] Mobile applications (iOS/Android)
- [ ] Advanced analytics dashboard
- [ ] Team collaboration features
- [ ] API webhooks