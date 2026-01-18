"""ChromaDB vector store operations."""

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Optional

from app.config import get_settings
from app.core.embeddings import get_embeddings


_vectorstore: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    """Get or create ChromaDB vector store instance.
    
    Returns:
        Chroma vector store with persistent storage
    """
    global _vectorstore
    
    if _vectorstore is None:
        settings = get_settings()
        embeddings = get_embeddings()
        
        # Initialize persistent ChromaDB client
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        _vectorstore = Chroma(
            client=client,
            collection_name=settings.COLLECTION_NAME,
            embedding_function=embeddings,
        )
    
    return _vectorstore


def add_documents(documents: List[Document]) -> List[str]:
    """Add documents to the vector store.
    
    Args:
        documents: List of LangChain Document objects
        
    Returns:
        List of document IDs
    """
    vectorstore = get_vectorstore()
    ids = vectorstore.add_documents(documents)
    return ids


def similarity_search(query: str, k: int = 4) -> List[Document]:
    """Perform similarity search on the vector store.
    
    Args:
        query: Search query string
        k: Number of documents to retrieve
        
    Returns:
        List of relevant documents
    """
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(query, k=k)


def similarity_search_with_score(query: str, k: int = 4) -> List[tuple]:
    """Perform similarity search with relevance scores.
    
    Args:
        query: Search query string
        k: Number of documents to retrieve
        
    Returns:
        List of (document, score) tuples
    """
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search_with_score(query, k=k)


def get_collection_stats() -> dict:
    """Get statistics about the vector store collection.
    
    Returns:
        Dictionary with collection statistics
    """
    vectorstore = get_vectorstore()
    collection = vectorstore._collection
    
    return {
        "name": collection.name,
        "count": collection.count(),
    }


def delete_collection():
    """Delete the entire collection. Use with caution."""
    global _vectorstore
    settings = get_settings()
    
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    try:
        client.delete_collection(settings.COLLECTION_NAME)
        _vectorstore = None
    except ValueError:
        pass  # Collection doesn't exist
