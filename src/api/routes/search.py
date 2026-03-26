from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi.util import get_remote_address
from src.models.schemas import SearchRequest, SearchResponse
from src.api.middlewares.auth import verify_api_key, limiter, get_index_service
from src.services.index_service import IndexService
from src.core.logger import setup_logging

logger = setup_logging()
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_products(
    request: Request,
    search_req: SearchRequest,
    api_key: str = Depends(verify_api_key),
    index_service: IndexService = Depends(get_index_service)
):
    """
    Search products using vector similarity + intent detection.
    
    - **query**: Search query string
    - **top_k**: Number of results (1-20)
    - **filters**: Optional attribute filters
    - **language**: Query language (en/fr/de)
    
    Returns ranked product results with similarity scores.
    """
    try:
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.info(f"Search request [{request_id}]: {search_req.query}")
        
        results = await index_service.search_service.search(search_req)
        return results
        
    except Exception as e:
        logger.error(f"Search failed [{request_id}]: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search operation failed: {str(e)}"
        )