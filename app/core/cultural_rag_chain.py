"""Cultural RAG chain with epistemic awareness.

This extends the standard RAG chain to use cultural retrieval strategies
that respect knowledge provenance and provide non-hegemonic perspectives.
"""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from app.core.llm import get_llm
from app.core.cultural_retriever import get_cultural_retriever, RetrievalStrategy
from app.prompts.templates import get_qa_prompt
from app.core.rag_chain import format_docs, extract_sources


def format_docs_with_metadata(docs: List[Document]) -> str:
    """Format documents with cultural metadata visible.
    
    Args:
        docs: Documents to format
        
    Returns:
        Formatted context with provenance information
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        
        # Source info
        source = meta.get("filename", "Unknown")
        source_type = meta.get("source_type", "unknown")
        authority = meta.get("authority_level", "unknown")
        origin = meta.get("epistemic_origin", "unknown")
        
        # Discourse info
        position = meta.get("discourse_position", "neutral")
        role = meta.get("chunk_role", "unknown")
        
        # Format with metadata
        header = f"[Sumber {i}: {source}]"
        prov_info = f"[Tipe: {source_type} | Otoritas: {authority} | Posisi: {position}]"
        
        formatted.append(f"{header}\n{prov_info}\n{doc.page_content}")
    
    return "\n\n---\n\n".join(formatted)


def extract_cultural_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    """Extract sources with cultural metadata.
    
    Args:
        docs: Documents with metadata
        
    Returns:
        List of source info with cultural context
    """
    sources = []
    for doc in docs:
        meta = doc.metadata
        source_info = {
            "filename": meta.get("filename"),
            "source_type": meta.get("source_type"),
            "authority_level": meta.get("authority_level"),
            "epistemic_origin": meta.get("epistemic_origin"),
            "discourse_position": meta.get("discourse_position"),
            "chunk_role": meta.get("chunk_role"),
            "themes": meta.get("themes", []),
            "language": meta.get("language"),
            "has_citation": meta.get("has_citation", False),
        }
        # Remove None values
        source_info = {k: v for k, v in source_info.items() if v is not None}
        sources.append(source_info)
    
    return sources


class CulturalRAGChain:
    """RAG chain with cultural awareness and epistemic filtering."""
    
    def __init__(
        self,
        k: int = 4,
        temperature: float = 0.7,
        boost_community: bool = True
    ):
        """Initialize cultural RAG chain.
        
        Args:
            k: Number of documents to retrieve
            temperature: LLM temperature
            boost_community: Whether to boost community sources
        """
        self.retriever = get_cultural_retriever()
        self.llm = get_llm(temperature=temperature)
        self.prompt = get_qa_prompt()
        self.k = k
        self.boost_community = boost_community
    
    def invoke(
        self,
        question: str,
        strategy: RetrievalStrategy = RetrievalStrategy.AUTHORITY_RANKED,
        **strategy_kwargs
    ) -> Dict[str, Any]:
        """Process question with cultural awareness.
        
        Args:
            question: User question
            strategy: Retrieval strategy to use
            **strategy_kwargs: Strategy-specific parameters
            
        Returns:
            Answer with cultural context
        """
        # Set defaults
        if "k" not in strategy_kwargs:
            strategy_kwargs["k"] = self.k
        if strategy == RetrievalStrategy.AUTHORITY_RANKED and "boost_community" not in strategy_kwargs:
            strategy_kwargs["boost_community"] = self.boost_community
        
        # Retrieve with cultural awareness
        docs = self.retriever.retrieve_cultural(
            query=question,
            strategy=strategy,
            **strategy_kwargs
        )
        
        # Format context
        context = format_docs_with_metadata(docs)
        
        # Generate answer
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        return {
            "answer": answer,
            "sources": extract_cultural_sources(docs),
            "strategy_used": strategy.value,
            "context_used": len(docs)
        }
    
    def invoke_plural(
        self,
        question: str,
        k_per_source: int = 2
    ) -> Dict[str, Any]:
        """Invoke with plural perspectives.
        
        Args:
            question: User question
            k_per_source: Documents per source type
            
        Returns:
            Answer synthesis from multiple perspectives
        """
        # Get cultural context with perspectives
        context_data = self.retriever.assemble_cultural_context(
            query=question,
            include_perspectives=True,
            boost_community=self.boost_community,
            k=self.k
        )
        
        # Format primary context
        primary_context = format_docs_with_metadata(context_data["primary_docs"])
        
        # Format perspectives
        perspectives_text = []
        for source_type, docs in context_data["perspectives"].items():
            if docs:
                perspectives_text.append(f"\n[Perspektif {source_type.upper()}]")
                for doc in docs:
                    perspectives_text.append(doc.page_content[:200] + "...")
        
        full_context = primary_context + "\n\n" + "\n".join(perspectives_text)
        
        # Generate answer
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": full_context,
            "question": question
        })
        
        return {
            "answer": answer,
            "sources": extract_cultural_sources(context_data["primary_docs"]),
            "perspectives": {
                k: extract_cultural_sources(v)
                for k, v in context_data["perspectives"].items()
            },
            "metadata_summary": context_data["metadata_summary"],
            "strategy_used": "plural_perspectives",
            "context_used": context_data["metadata_summary"]["total_documents"]
        }
    
    def invoke_epistemic(
        self,
        question: str,
        source_type: Optional[str] = None,
        authority_level: Optional[str] = None,
        k: Optional[int] = None
    ) -> Dict[str, Any]:
        """Invoke with epistemic filtering.
        
        Args:
            question: User question
            source_type: Filter by source (community/academic/media)
            authority_level: Filter by authority
            k: Number of documents
            
        Returns:
            Answer from filtered sources
        """
        docs = self.retriever.retrieve_epistemic(
            query=question,
            source_type=source_type,
            authority_level=authority_level,
            k=k or self.k
        )
        
        context = format_docs_with_metadata(docs)
        
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        filters_used = {}
        if source_type:
            filters_used["source_type"] = source_type
        if authority_level:
            filters_used["authority_level"] = authority_level
        
        return {
            "answer": answer,
            "sources": extract_cultural_sources(docs),
            "strategy_used": "epistemic_filtered",
            "filters_applied": filters_used,
            "context_used": len(docs)
        }


def get_cultural_rag_chain(
    k: int = 4,
    temperature: float = 0.7,
    boost_community: bool = True
) -> CulturalRAGChain:
    """Factory function for cultural RAG chain.
    
    Args:
        k: Number of documents to retrieve
        temperature: LLM temperature
        boost_community: Boost community sources
        
    Returns:
        CulturalRAGChain instance
    """
    return CulturalRAGChain(k=k, temperature=temperature, boost_community=boost_community)
