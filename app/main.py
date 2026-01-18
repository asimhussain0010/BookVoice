"""
FastAPI Application Entry Point
Main application configuration and routing
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.config import settings
from app.database import init_db
from app.api import auth, books, audio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting BookVoice application...")
    
    # Initialize database
    init_db()
    
    # Create necessary directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    os.makedirs("app/static/css", exist_ok=True)
    os.makedirs("app/static/js", exist_ok=True)
    
    print("Database initialized successfully")
    print(f"Upload directory: {settings.UPLOAD_DIR}")
    print(f"Audio directory: {settings.AUDIO_DIR}")
    
    yield
    
    # Shutdown
    print("Shutting down BookVoice application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade eBook to Audio conversion platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(books.router, prefix=settings.API_PREFIX)
app.include_router(audio.router, prefix=settings.API_PREFIX)


# Web Routes (HTML Pages)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page - redirect to login"""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("auth/register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard"""
    return templates.TemplateResponse("dashboard/index.html", {"request": request})


@app.get("/books/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Book upload page"""
    return templates.TemplateResponse("books/upload.html", {"request": request})


@app.get("/books/{book_id}", response_class=HTMLResponse)
async def book_detail_page(request: Request, book_id: int):
    """Book detail page"""
    return templates.TemplateResponse(
        "books/detail.html",
        {"request": request, "book_id": book_id}
    )


# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# API documentation redirect
@app.get("/api")
def api_redirect():
    """Redirect to API documentation"""
    return {"message": "Visit /docs for API documentation"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS
    )