from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from slowapi.util import get_remote_address
from src.models.schemas import ChatRequest, ChatResponse
from src.api.middlewares.auth import verify_api_key, limiter, get_index_service
from src.services.index_service import IndexService
from src.core.logger import setup_logging

from fastapi import Query
from src.core.config import settings

logger = setup_logging()
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat_endpoint(
    request: Request,
    chat_req: ChatRequest,
    api_key: str = Depends(verify_api_key),
    index_service: IndexService = Depends(get_index_service)
):
    """
    Conversational chat endpoint with memory and RAG.
    
    - **message**: User message
    - **session_id**: Optional session ID for continuity
    - **language**: Language code
    - **context**: Optional additional context
    
    Returns AI response with sources and session ID.
    """
    try:
        request_id = getattr(request.state, 'request_id', 'unknown')
        logger.info(f"Chat request [{request_id}]: {chat_req.message[:50]}...")
        
        response = await index_service.chat_service.chat(chat_req)
        return response
        
    except Exception as e:
        logger.error(f"Chat failed [{request_id}]: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat operation failed: {str(e)}"
        )

# WebSocket alternative for real-time chat
@router.websocket("/chat/ws")
async def websocket_chat(
    websocket: WebSocket,
    api_key: str = Query(...),  # API key via query param for WS
):
    """WebSocket endpoint for real-time chat (optional)"""
    await websocket.accept()
    
    try:
        # Verify API key
        if api_key != settings.API_KEY:
            await websocket.close(code=1008, reason="Invalid API Key")
            return
            
        while True:
            data = await websocket.receive_json()
            chat_req = ChatRequest(**data)
            
            # Process through chat service
            response = await index_service.chat_service.chat(chat_req)
            
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal error")

