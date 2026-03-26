from fastapi import APIRouter, Depends
from datetime import datetime
import time
from src.models.schemas import HealthStatus
from src.api.middlewares.auth import get_optional_api_key
from src.core.config import settings

router = APIRouter()

# Track startup time
START_TIME = time.time()

@router.get("/health", response_model=HealthStatus)
async def health_check(api_key: str = Depends(get_optional_api_key)):
    """Health check endpoint - public or protected based on config"""
    
    # Check services
    services = {
        "faiss_index": True,  # Would check actual file existence
        "redis": True,        # Would ping Redis
        "openai": bool(settings.OPENAI_API_KEY),
        "magento": bool(settings.MAGENTO_API_TOKEN)
    }
    
    # Determine overall status
    if all(services.values()):
        status = "healthy"
    elif sum(services.values()) >= len(services) / 2:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthStatus(
        status=status,
        version="0.7.0",
        timestamp=datetime.utcnow(),
        services=services,
        uptime_seconds=time.time() - START_TIME
    )

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    return {"ready": True}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    return {"alive": True}