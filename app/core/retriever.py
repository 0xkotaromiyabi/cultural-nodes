"""Retriever for RAG pipeline."""

from langchain_core.documents import Document
from typing import List

from app.config import get_settings
from app.core.vectorstore import get_vectorstore


class CulturalRetriever:
    """Retriever for cultural studies knowledge base."""
    
    def __init__(self, k: int = None):
        """Initialize retriever.
        
        Args:
            k: Number of documents to retrieve (default from settings)
        """
        settings = get_settings()
        self.k = k or settings.RETRIEVAL_K
        self.vectorstore = get_vectorstore()
    
    def retrieve(self, query: str) -> List[Document]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: User query string
            
        Returns:
            List of relevant documents
        """
        return self.vectorstore.similarity_search(query, k=self.k)
    
    def retrieve_with_scores(self, query: str) -> List[tuple]:
        """Retrieve documents with relevance scores.
        
        Args:
            query: User query string
            
        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(query, k=self.k)
    
    def get_as_langchain_retriever(self):
        """Get as LangChain retriever for use in chains.
        
        Returns:
            LangChain VectorStoreRetriever
        """
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.k}
        )


def get_retriever(k: int = None) -> CulturalRetriever:
    """Factory function to get retriever instance.
    
    Args:
        k: Number of documents to retrieve
        
    Returns:
        CulturalRetriever instance
    """
    return CulturalRetriever(k=k)
