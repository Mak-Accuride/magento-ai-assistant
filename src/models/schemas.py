from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Enums
class IntentType(str, Enum):
    PRODUCT_SEARCH = "product_search"
    COMPARISON = "comparison"
    SPECIFICATION = "specification"
    GENERAL = "general"
    CLARIFICATION = "clarification"

class LanguageCode(str, Enum):
    EN = "en"
    FR = "fr"
    DE = "de"

# Search Models
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="User search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (category, price_range, etc.)")
    language: LanguageCode = Field(default=LanguageCode.EN, description="Query language")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "refrigerator with ice maker",
                "top_k": 5,
                "language": "en",
                "filters": {"category": "appliances", "in_stock": True}
            }
        }

class ProductResult(BaseModel):
    product_id: str
    name: str
    sku: str
    description: str
    price: float
    category: str
    attributes: Dict[str, Any]
    score: float = Field(..., description="Similarity score (0-1)")
    source: Literal["vector", "keyword", "hybrid"] = "vector"

class SearchResponse(BaseModel):
    query: str
    results: List[ProductResult]
    total_found: int
    processing_time_ms: float
    intent_detected: Optional[IntentType] = None
    suggestions: Optional[List[str]] = None

# Chat Models
class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    language: LanguageCode = LanguageCode.EN
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Which refrigerator has the largest capacity?",
                "session_id": "sess_123abc",
                "language": "en"
            }
        }

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[ProductResult] = []
    intent: IntentType
    confidence: float
    suggested_followups: List[str] = []
    conversation_length: int

# Health Check
class HealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime
    services: Dict[str, bool]
    uptime_seconds: float