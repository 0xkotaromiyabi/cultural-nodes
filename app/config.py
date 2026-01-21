"""Configuration settings for Cultural AI RAG system."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # ChromaDB settings
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    COLLECTION_NAME: str = "cultural_knowledge"
    
    # Knowledge Store settings (Cultural Nodes)
    KNOWLEDGE_STORE_PATH: str = "./data/cultural_knowledge.db"
    
    # Chunking settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    USE_DISCOURSE_CHUNKING: bool = True  # Enable discourse-aware chunking
    
    # Embedding versioning
    EMBEDDING_VERSION: str = ""  # Auto-generated if empty
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Retrieval settings
    RETRIEVAL_K: int = 4  # Number of documents to retrieve
    
    # Curatorial policy
    CURATORIAL_POLICY: str = "cultural"  # Default policy
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
