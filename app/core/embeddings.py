"""Embeddings service using Ollama."""

from langchain_ollama import OllamaEmbeddings
from app.config import get_settings


def get_embeddings() -> OllamaEmbeddings:
    """Get Ollama embeddings instance.
    
    Returns:
        OllamaEmbeddings configured with nomic-embed-text model
    """
    settings = get_settings()
    
    return OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
