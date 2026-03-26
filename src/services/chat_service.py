import uuid
import json
import redis
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import openai

from src.models.schemas import ChatRequest, ChatResponse, ChatMessage, ProductResult, IntentType
from src.services.search_service import SearchService
from src.core.config import settings
from src.core.logger import setup_logging

logger = setup_logging()

class ChatService:
    """Conversational AI with memory and RAG"""
    
    def __init__(self, search_service: SearchService):
        self.search_service = search_service
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        openai.api_key = settings.OPENAI_API_KEY
        
    def get_session_memory(self, session_id: str) -> List[Dict]:
        """Retrieve conversation history from Redis (Week 5)"""
        key = f"chat:session:{session_id}"
        history = self.redis_client.get(key)
        
        if history:
            return json.loads(history)
        return []
    
    def save_session_memory(self, session_id: str, history: List[Dict]):
        """Save conversation history to Redis with TTL"""
        key = f"chat:session:{session_id}"
        self.redis_client.setex(
            key, 
            settings.SESSION_TIMEOUT,
            json.dumps(history, default=str)
        )
    
    def format_context(self, products: List[ProductResult]) -> str:
        """Format product results for LLM context (Week 4)"""
        context_parts = []
        for p in products:
            attrs = ", ".join([f"{k}: {v}" for k, v in p.attributes.items()])
            context_parts.append(
                f"Product: {p.name} (ID: {p.product_id})\\n"
                f"Price: ${p.price} | Category: {p.category}\\n"
                f"Description: {p.description}\\n"
                f"Attributes: {attrs}\\n"
            )
        return "\\n---\\n".join(context_parts)
    
    async def generate_response(
        self, 
        query: str, 
        context: str, 
        history: List[Dict],
        intent: IntentType
    ) -> str:
        """Generate LLM response with RAG context (Week 4)"""
        
        # Build messages
        messages = [
            {"role": "system", "content": self._get_system_prompt(intent)}
        ]
        
        # Add conversation history (last 5 exchanges)
        for msg in history[-settings.MAX_HISTORY_LENGTH:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current query with context
        prompt = f"""Based on the following product information, answer the user's question:

Available Products:
{context}

User Question: {query}

Provide a helpful, conversational response. If comparing products, highlight key differences."""

        messages.append({"role": "user", "content": prompt})
        
        try:
            response = openai.ChatCompletion.create(
                model=settings.LLM_MODEL,
                messages=messages,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"I found some relevant products, but I'm having trouble generating a detailed response. Here are the top matches: {context[:200]}..."
    
    def _get_system_prompt(self, intent: IntentType) -> str:
        """Get intent-specific system prompt"""
        base = "You are a helpful AI assistant for an e-commerce product search. "
        
        prompts = {
            IntentType.COMPARISON: base + "Focus on comparing product features, pros and cons.",
            IntentType.SPECIFICATION: base + "Provide detailed technical specifications.",
            IntentType.PRODUCT_SEARCH: base + "Help users find the best products for their needs.",
            IntentType.GENERAL: base + "Answer general questions about products helpfully."
        }
        return prompts.get(intent, prompts[IntentType.GENERAL])
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process chat message with memory and RAG"""
        
        # Generate or use existing session ID
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"
        
        # Get conversation history
        history = self.get_session_memory(session_id)
        
        # Detect intent
        intent = self.search_service.detect_intent(request.message)
        
        # Perform search for context
        from src.models.schemas import SearchRequest
        search_req = SearchRequest(
            query=request.message,
            top_k=3,
            language=request.language
        )
        search_results = await self.search_service.search(search_req)
        
        # Format context
        context = self.format_context(search_results.results)
        
        # Generate response
        response_text = await self.generate_response(
            request.message,
            context,
            history,
            intent
        )
        
        # Update history
        history.append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        history.append({
            "role": "assistant", 
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": [p.product_id for p in search_results.results]
        })
        
        # Save updated history
        self.save_session_memory(session_id, history)
        
        # Generate follow-up suggestions
        followups = []
        if search_results.results:
            followups = [
                f"Tell me more about {search_results.results[0].name}",
                "Compare the top 2 results",
                "What's the price range?"
            ]
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=search_results.results,
            intent=intent,
            confidence=search_results.results[0].score if search_results.results else 0.0,
            suggested_followups=followups[:3],
            conversation_length=len(history) // 2
        )
    
    async def close(self):
        """Cleanup"""
        self.redis_client.close()