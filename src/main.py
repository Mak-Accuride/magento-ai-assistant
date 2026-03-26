
# File 1: Main FastAPI Application (Monday: fastapi-init)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from src.api.routes import search, chat, health
from src.core.config import settings
from src.core.logger import setup_logging
from src.services.index_service import IndexService

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events"""
    # Startup: Load FAISS index and dependencies
    logger.info("🚀 Starting up Week 7 API Layer...")
    try:
        index_service = IndexService()
        await index_service.initialize()
        app.state.index_service = index_service
        logger.info("✅ FAISS index and services initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup
    logger.info("🛑 Shutting down API...")
    if hasattr(app.state, 'index_service'):
        await app.state.index_service.close()

# Initialize FastAPI app
app = FastAPI(
    title="AI Magento Conversational Search API",
    description="Week 7 Deliverable: FastAPI backend for RAG-based product search with conversational memory",
    version="0.7.0",
    docs_url="/docs" if not settings.PRODUCTION else None,
    redoc_url="/redoc" if not settings.PRODUCTION else None,
    openapi_url="/openapi.json" if not settings.PRODUCTION else None,
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*", "X-API-Key", "Authorization"],
    expose_headers=["X-Request-ID"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    import uuid
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.get("/")
async def root():
    return {
        "message": "AI Magento Search API - Week 7",
        "version": "0.7.0",
        "docs": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )

