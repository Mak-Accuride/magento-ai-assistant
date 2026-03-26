import time
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import faiss
import json
import pickle

from src.models.schemas import SearchRequest, SearchResponse, ProductResult, IntentType
from src.core.config import settings
from src.core.logger import setup_logging

logger = setup_logging()

class SearchService:
    """Hybrid search service combining vector + keyword search"""
    
    def __init__(self):
        self.model = None
        self.index = None
        self.product_metadata = {}
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
    async def initialize(self):
        """Load FAISS index and embedding model"""
        logger.info("Initializing Search Service...")
        
        # Load embedding model (Week 3)
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        # Load FAISS index
        try:
            self.index = faiss.read_index(settings.FAISS_INDEX_PATH)
            
            # Load metadata mapping
            with open(f"{settings.DATA_DIR}/product_metadata.pkl", "rb") as f:
                self.product_metadata = pickle.load(f)
                
            logger.info(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            # Initialize empty index for development
            self.index = faiss.IndexFlatIP(self.dimension)
            
    def detect_intent(self, query: str) -> IntentType:
        """Week 5: Intent classification"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference between"]):
            return IntentType.COMPARISON
        elif any(word in query_lower for word in ["spec", "dimension", "size", "weight", "capacity"]):
            return IntentType.SPECIFICATION
        elif any(word in query_lower for word in ["which", "what", "best", "recommend"]):
            return IntentType.PRODUCT_SEARCH
        else:
            return IntentType.GENERAL
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute hybrid search"""
        start_time = time.time()
        
        # Detect intent (Week 5)
        intent = self.detect_intent(request.query)
        
        # Generate embedding (Week 3)
        query_embedding = self.model.encode([request.query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # FAISS search
        scores, indices = self.index.search(query_embedding, request.top_k * 2)
        
        # Build results
        results = []
        seen_ids = set()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.product_metadata):
                continue
                
            product_id = str(list(self.product_metadata.keys())[idx])
            if product_id in seen_ids:
                continue
            seen_ids.add(product_id)
            
            metadata = self.product_metadata.get(product_id, {})
            
            # Apply filters if provided
            if request.filters:
                skip = False
                for key, value in request.filters.items():
                    if metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            
            results.append(ProductResult(
                product_id=product_id,
                name=metadata.get("name", "Unknown"),
                sku=metadata.get("sku", ""),
                description=metadata.get("description", "")[:200],
                price=metadata.get("price", 0.0),
                category=metadata.get("category", "general"),
                attributes=metadata.get("attributes", {}),
                score=float(score),
                source="vector"
            ))
            
            if len(results) >= request.top_k:
                break
        
        processing_time = (time.time() - start_time) * 1000
        
        # Generate suggestions based on intent
        suggestions = None
        if intent == IntentType.COMPARISON and len(results) >= 2:
            suggestions = [f"Compare {results[0].name} vs {results[1].name}"]
        elif len(results) > 0:
            suggestions = [f"Show specifications for {results[0].name}"]
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            processing_time_ms=processing_time,
            intent_detected=intent,
            suggestions=suggestions
        )
    
    async def close(self):
        """Cleanup resources"""
        pass