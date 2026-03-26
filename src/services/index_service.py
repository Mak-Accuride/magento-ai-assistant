from src.services.search_service import SearchService
from src.services.chat_service import ChatService
from src.core.logger import setup_logging

logger = setup_logging()

class IndexService:
    """Centralized service manager for index and chat"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.chat_service = None
        
    async def initialize(self):
        """Initialize all services"""
        await self.search_service.initialize()
        self.chat_service = ChatService(self.search_service)
        logger.info("✅ All services initialized")
        
    async def close(self):
        """Cleanup all services"""
        await self.search_service.close()
        if self.chat_service:
            await self.chat_service.close()
        logger.info("✅ All services closed")