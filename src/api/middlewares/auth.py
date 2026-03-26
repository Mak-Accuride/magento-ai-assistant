from fastapi import Security, HTTPException, status, Request, Depends
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.core.config import settings
from src.core.logger import setup_logging

logger = setup_logging()

# Rate limiter setup
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

# API Key security
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    """Verify API key from header"""
    if not api_key:
        logger.warning(f"Missing API key - Request ID: {getattr(request.state, 'request_id', 'unknown')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # In production, use secure comparison (constant time)
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key provided - Request ID: {getattr(request.state, 'request_id', 'unknown')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    return api_key

async def get_optional_api_key(api_key: str = Security(api_key_header)):
    """Optional API key for health checks or public endpoints"""
    return api_key

# Dependency injection for services
async def get_index_service(request: Request):
    """Get initialized index service from app state"""
    if not hasattr(request.app.state, 'index_service'):
        raise HTTPException(status_code=503, detail="Search service unavailable")
    return request.app.state.index_service