"""Ollama LLM wrapper for llama3.1."""

from langchain_ollama import OllamaLLM
from langchain_core.language_models.base import BaseLanguageModel

from app.config import get_settings


def get_llm(temperature: float = 0.7) -> BaseLanguageModel:
    """Get Ollama LLM instance.
    
    Args:
        temperature: Model temperature (0.0-1.0)
        
    Returns:
        OllamaLLM configured with llama3.1 model
    """
    settings = get_settings()
    
    return OllamaLLM(
        model=settings.LLM_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature,
    )
