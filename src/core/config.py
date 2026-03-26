from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-Magento-Search"
    DEBUG: bool = False
    PRODUCTION: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    API_KEY: str = "dev-key-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Magento (from Week 1-2)
    MAGENTO_BASE_URL: str = "https://magento.example.com"
    MAGENTO_API_TOKEN: str = ""
    
    # FAISS/Embeddings (from Week 3)
    FAISS_INDEX_PATH: str = "./data/faiss_index.bin"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM (from Week 4)
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    
    # Memory/Session (from Week 5)
    REDIS_URL: str = "redis://localhost:6379/0"
    SESSION_TIMEOUT: int = 3600  # 1 hour
    MAX_HISTORY_LENGTH: int = 10
    
    # Paths
    DATA_DIR: str = "./data"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()