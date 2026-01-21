"""Cultural Retrieval Layer - Epistemically-aware search and retrieval.

This module implements retrieval strategies that respect knowledge provenance,
authority levels, and cultural context. Unlike standard RAG that only uses
similarity, this retriever can:

1. Filter by epistemic origin (community vs academic vs institutional)
2. Retrieve plural perspectives (non-hegemonic)
3. Rank by authority level
4. Assemble context with cultural awareness
5. Balance different discourse positions
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from langchain_core.documents import Document

from app.core.vectorstore import similarity_search_with_score, get_vectorstore
from app.core.knowledge_store import get_knowledge_store
from app.config import get_settings


class RetrievalStrategy(str, Enum):
    """Retrieval strategy types."""
    STANDARD = "standard"  # Standard similarity search
    EPISTEMIC = "epistemic"  # Filter by epistemic origin
    PLURAL = "plural"  # Multiple perspectives
    AUTHORITY_RANKED = "authority_ranked"  # Ranked by authority
    DISCOURSE_BALANCED = "discourse_balanced"  # Balance discourse positions


class CulturalRetriever:
    """Culturally-aware retrieval that respects knowledge provenance."""
    
    # Authority level hierarchy (for ranking)
    AUTHORITY_WEIGHTS = {
        "situated": 1.2,  # Boost community knowledge
        "academic": 1.0,
        "media": 0.9,
        "institutional": 0.8,
        "archival": 1.1,
    }
    
    def __init__(self):
        """Initialize cultural retriever."""
        self.vectorstore = get_vectorstore()
        self.knowledge_store = get_knowledge_store()
        self.settings = get_settings()
    
    def retrieve_standard(
        self,
        query: str,
        k: int = 4
    ) -> List[Document]:
        """Standard similarity-based retrieval (baseline).
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of documents
        """
        docs_with_scores = similarity_search_with_score(query, k=k)
        return [doc for doc, score in docs_with_scores]
    
    def retrieve_epistemic(
        self,
        query: str,
        epistemic_origin: Optional[str] = None,
        source_type: Optional[str] = None,
        authority_level: Optional[str] = None,
        k: int = 4
    ) -> List[Document]:
        """Retrieve documents filtered by epistemic criteria.
        
        Args:
            query: Search query
            epistemic_origin: Filter by origin (e.g., "local_knowledge")
            source_type: Filter by source (e.g., "community")
            authority_level: Filter by authority (e.g., "situated")
            k: Number of documents
            
        Returns:
            Filtered documents
        """
        # Get candidate documents from vector store
        candidates_with_scores = similarity_search_with_score(query, k=k*3)
        
        # Filter by metadata
        filtered_docs = []
        for doc, score in candidates_with_scores:
            metadata = doc.metadata
            
            # Apply filters
            if epistemic_origin and metadata.get("epistemic_origin") != epistemic_origin:
                continue
            if source_type and metadata.get("source_type") != source_type:
                continue
            if authority_level and metadata.get("authority_level") != authority_level:
                continue
            
            filtered_docs.append((doc, score))
            
            if len(filtered_docs) >= k:
                break
        
        return [doc for doc, score in filtered_docs]
    
    def retrieve_plural(
        self,
        query: str,
        k_per_source: int = 2
    ) -> Dict[str, List[Document]]:
        """Retrieve multiple perspectives from different sources.
        
        This implements non-hegemonic retrieval by getting documents
        from different authority levels and epistemic origins.
        
        Args:
            query: Search query
            k_per_source: Documents per source type
            
        Returns:
            Dictionary mapping source types to documents
        """
        source_types = ["community", "academic", "media", "archival"]
        results = {}
        
        for source_type in source_types:
            docs = self.retrieve_epistemic(
                query=query,
                source_type=source_type,
                k=k_per_source
            )
            if docs:
                results[source_type] = docs
        
        return results
    
    def retrieve_authority_ranked(
        self,
        query: str,
        boost_community: bool = True,
        k: int = 4
    ) -> List[Document]:
        """Retrieve and rank by authority level.
        
        Args:
            query: Search query
            boost_community: Whether to boost community sources
            k: Number of documents
            
        Returns:
            Ranked documents
        """
        # Get candidates
        candidates_with_scores = similarity_search_with_score(query, k=k*2)
        
        # Re-rank by authority
        ranked = []
        for doc, sim_score in candidates_with_scores:
            authority = doc.metadata.get("authority_level", "academic")
            
            # Apply authority weight
            weight = self.AUTHORITY_WEIGHTS.get(authority, 1.0)
            if boost_community and authority == "situated":
                weight *= 1.3  # Extra boost for community
            
            final_score = sim_score * weight
            ranked.append((doc, final_score))
        
        # Sort by final score
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in ranked[:k]]
    
    def retrieve_discourse_balanced(
        self,
        query: str,
        k: int = 4
    ) -> List[Document]:
        """Retrieve documents with balanced discourse positions.
        
        Ensures diversity of perspectives: supportive, critical, neutral, questioning.
        
        Args:
            query: Search query
            k: Number of documents
            
        Returns:
            Documents with balanced discourse positions
        """
        candidates_with_scores = similarity_search_with_score(query, k=k*3)
        
        # Group by discourse position
        by_position = {
            "critical": [],
            "supportive": [],
            "neutral": [],
            "questioning": []
        }
        
        for doc, score in candidates_with_scores:
            position = doc.metadata.get("discourse_position", "neutral")
            if position in by_position:
                by_position[position].append((doc, score))
        
        # Balance selection
        balanced = []
        positions = ["critical", "supportive", "neutral", "questioning"]
        
        # Round-robin selection to ensure balance
        max_per_position = max(1, k // len(positions))
        for position in positions:
            docs = by_position[position][:max_per_position]
            balanced.extend(docs)
        
        # Sort by score and take top k
        balanced.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in balanced[:k]]
    
    def retrieve_by_theme(
        self,
        query: str,
        required_themes: List[str],
        k: int = 4
    ) -> List[Document]:
        """Retrieve documents that match specific themes.
        
        Args:
            query: Search query
            required_themes: Themes that must be present
            k: Number of documents
            
        Returns:
            Documents matching themes
        """
        candidates_with_scores = similarity_search_with_score(query, k=k*3)
        
        filtered = []
        for doc, score in candidates_with_scores:
            doc_themes = doc.metadata.get("themes", [])
            
            # Check if all required themes are present
            if all(theme in doc_themes for theme in required_themes):
                filtered.append((doc, score))
            
            if len(filtered) >= k:
                break
        
        return [doc for doc, score in filtered]
    
    def retrieve_cultural(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.STANDARD,
        **kwargs
    ) -> List[Document]:
        """Main retrieval method with strategy selection.
        
        Args:
            query: Search query
            strategy: Retrieval strategy to use
            **kwargs: Strategy-specific parameters
            
        Returns:
            Retrieved documents
        """
        if strategy == RetrievalStrategy.STANDARD:
            return self.retrieve_standard(query, k=kwargs.get("k", 4))
        
        elif strategy == RetrievalStrategy.EPISTEMIC:
            return self.retrieve_epistemic(
                query=query,
                epistemic_origin=kwargs.get("epistemic_origin"),
                source_type=kwargs.get("source_type"),
                authority_level=kwargs.get("authority_level"),
                k=kwargs.get("k", 4)
            )
        
        elif strategy == RetrievalStrategy.PLURAL:
            # Returns dict, so convert to list
            results = self.retrieve_plural(
                query=query,
                k_per_source=kwargs.get("k_per_source", 2)
            )
            # Flatten dict to list
            all_docs = []
            for docs in results.values():
                all_docs.extend(docs)
            return all_docs
        
        elif strategy == RetrievalStrategy.AUTHORITY_RANKED:
            return self.retrieve_authority_ranked(
                query=query,
                boost_community=kwargs.get("boost_community", True),
                k=kwargs.get("k", 4)
            )
        
        elif strategy == RetrievalStrategy.DISCOURSE_BALANCED:
            return self.retrieve_discourse_balanced(
                query=query,
                k=kwargs.get("k", 4)
            )
        
        else:
            # Fallback to standard
            return self.retrieve_standard(query, k=kwargs.get("k", 4))
    
    def assemble_cultural_context(
        self,
        query: str,
        include_perspectives: bool = True,
        boost_community: bool = True,
        k: int = 4
    ) -> Dict:
        """Assemble culturally-aware context for RAG.
        
        This is the main method for cultural RAG - it retrieves documents
        with awareness of provenance and assembles them with metadata.
        
        Args:
            query: User query
            include_perspectives: Whether to include plural perspectives
            boost_community: Whether to boost community sources
            k: Total documents to retrieve
            
        Returns:
            Dictionary with documents and metadata
        """
        result = {
            "query": query,
            "primary_docs": [],
            "perspectives": {},
            "metadata_summary": {}
        }
        
        # Primary retrieval with authority ranking
        primary_docs = self.retrieve_authority_ranked(
            query=query,
            boost_community=boost_community,
            k=k
        )
        result["primary_docs"] = primary_docs
        
        # Add plural perspectives if requested
        if include_perspectives:
            perspectives = self.retrieve_plural(
                query=query,
                k_per_source=1
            )
            result["perspectives"] = perspectives
        
        # Summarize metadata
        all_docs = primary_docs
        if include_perspectives:
            for docs in perspectives.values():
                all_docs.extend(docs)
        
        # Count sources
        source_counts = {}
        authority_counts = {}
        discourse_counts = {}
        themes_counts = {}
        
        for doc in all_docs:
            meta = doc.metadata
            
            source = meta.get("source_type", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
            
            authority = meta.get("authority_level", "unknown")
            authority_counts[authority] = authority_counts.get(authority, 0) + 1
            
            discourse = meta.get("discourse_position", "unknown")
            discourse_counts[discourse] = discourse_counts.get(discourse, 0) + 1
            
            themes = meta.get("themes", [])
            for theme in themes:
                themes_counts[theme] = themes_counts.get(theme, 0) + 1
        
        result["metadata_summary"] = {
            "total_documents": len(all_docs),
            "by_source": source_counts,
            "by_authority": authority_counts,
            "by_discourse": discourse_counts,
            "themes": themes_counts
        }
        
        return result


def get_cultural_retriever() -> CulturalRetriever:
    """Factory function to get cultural retriever.
    
    Returns:
        CulturalRetriever instance
    """
    return CulturalRetriever()
