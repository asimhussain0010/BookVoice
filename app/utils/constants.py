"""
Application Constants
Central location for all application constants
"""

# File Upload Constants
ALLOWED_FILE_TYPES = {'.pdf', '.epub', '.txt', '.docx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# MIME Types
MIME_TYPES = {
    'pdf': 'application/pdf',
    'epub': 'application/epub+zip',
    'txt': 'text/plain',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# Text Processing Constants
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 500000  # 500K characters
CHUNK_SIZE = 5000  # Characters per TTS chunk

# Audio Constants
SUPPORTED_AUDIO_FORMATS = ['mp3', 'wav', 'ogg']
DEFAULT_AUDIO_FORMAT = 'mp3'
DEFAULT_AUDIO_BITRATE = '128k'

# Language Support
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish'
}

# TTS Voice Options
TTS_VOICES = {
    'en': [
        'en-US-Standard-A',
        'en-US-Standard-B',
        'en-US-Standard-C',
        'en-US-Standard-D',
        'en-GB-Standard-A',
        'en-GB-Standard-B'
    ],
    'es': [
        'es-ES-Standard-A',
        'es-US-Standard-A'
    ],
    'fr': [
        'fr-FR-Standard-A',
        'fr-FR-Standard-B'
    ],
    'de': [
        'de-DE-Standard-A',
        'de-DE-Standard-B'
    ]
}

# Speed Options
SPEED_OPTIONS = {
    'very_slow': 0.5,
    'slow': 0.75,
    'normal': 1.0,
    'fast': 1.25,
    'very_fast': 1.5
}

# Status Constants
BOOK_STATUS = {
    'UPLOADED': 'uploaded',
    'PROCESSING': 'processing',
    'READY': 'ready',
    'ERROR': 'error'
}

AUDIO_STATUS = {
    'PENDING': 'pending',
    'PROCESSING': 'processing',
    'COMPLETED': 'completed',
    'FAILED': 'failed'
}

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 3600  # 1 hour
CACHE_TTL_LONG = 86400  # 24 hours

# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 100
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = False

# Username Requirements
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50

# Error Messages
ERROR_MESSAGES = {
    'INVALID_CREDENTIALS': 'Invalid email or password',
    'EMAIL_TAKEN': 'Email already registered',
    'USERNAME_TAKEN': 'Username already taken',
    'INVALID_TOKEN': 'Invalid or expired token',
    'UNAUTHORIZED': 'Authentication required',
    'FORBIDDEN': 'Permission denied',
    'NOT_FOUND': 'Resource not found',
    'FILE_TOO_LARGE': 'File exceeds maximum size',
    'INVALID_FILE_TYPE': 'File type not supported',
    'PROCESSING_ERROR': 'Error processing file',
    'GENERATION_ERROR': 'Error generating audio',
    'RATE_LIMIT': 'Too many requests. Please try again later.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'REGISTRATION': 'Account created successfully',
    'LOGIN': 'Login successful',
    'LOGOUT': 'Logged out successfully',
    'UPLOAD': 'Book uploaded successfully',
    'GENERATION_STARTED': 'Audio generation started',
    'GENERATION_COMPLETE': 'Audio generation completed',
    'UPDATE': 'Updated successfully',
    'DELETE': 'Deleted successfully'
}

# File Paths
UPLOAD_DIRECTORY = './uploads'
AUDIO_DIRECTORY = './app/static/audio'
LOG_DIRECTORY = './logs'
TEMP_DIRECTORY = './tmp'

# Logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# API Configuration
API_VERSION = 'v1'
API_PREFIX = f'/api/{API_VERSION}'

# CORS
CORS_ALLOW_ORIGINS = ['http://localhost:3000', 'http://localhost:8000']
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
CORS_ALLOW_HEADERS = ['*']

# Database
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 40
DB_POOL_RECYCLE = 3600

# Celery
CELERY_TASK_SOFT_TIME_LIMIT = 3300  # 55 minutes
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour
CELERY_TASK_MAX_RETRIES = 3

# Email (for future use)
EMAIL_FROM = 'noreply@bookvoice.com'
EMAIL_TEMPLATES = {
    'WELCOME': 'welcome.html',
    'RESET_PASSWORD': 'reset_password.html',
    'AUDIO_READY': 'audio_ready.html'
}

# Feature Flags
FEATURES = {
    'REGISTRATION_ENABLED': True,
    'EMAIL_VERIFICATION_REQUIRED': False,
    'ANALYTICS_ENABLED': False,
    'SOCIAL_LOGIN_ENABLED': False,
    'API_DOCS_ENABLED': True
}

# System Limits
MAX_BOOKS_PER_USER = 100
MAX_AUDIO_PER_BOOK = 5
MAX_CONCURRENT_GENERATIONS = 3

# Reading Time Calculation
WORDS_PER_MINUTE = {
    'slow': 150,
    'average': 200,
    'fast': 250
}

# Storage Quotas (future use)
STORAGE_QUOTA_FREE = 1 * 1024 * 1024 * 1024  # 1 GB
STORAGE_QUOTA_PREMIUM = 10 * 1024 * 1024 * 1024  # 10 GB

# Monitoring
HEALTH_CHECK_TIMEOUT = 5  # seconds
METRICS_COLLECTION_INTERVAL = 60  # seconds

# Default Values
DEFAULT_LANGUAGE = 'en'
DEFAULT_VOICE = 'en-US-Standard-A'
DEFAULT_SPEED = 1.0
DEFAULT_FORMAT = 'mp3'