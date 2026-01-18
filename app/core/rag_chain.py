"""RAG chain combining retrieval and generation."""

from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.core.llm import get_llm
from app.core.retriever import get_retriever
from app.prompts.templates import get_qa_prompt, get_analysis_prompt, get_linguistic_prompt


def format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into context string.
    
    Args:
        docs: List of retrieved documents
        
    Returns:
        Formatted context string
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("filename", doc.metadata.get("url", "Unknown"))
        formatted.append(f"[Sumber {i}: {source}]\n{doc.page_content}")
    
    return "\n\n---\n\n".join(formatted)


def extract_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    """Extract source information from documents.
    
    Args:
        docs: List of documents
        
    Returns:
        List of source metadata dictionaries
    """
    sources = []
    for doc in docs:
        source_info = {
            "filename": doc.metadata.get("filename"),
            "source_type": doc.metadata.get("source_type"),
            "url": doc.metadata.get("url"),
            "page": doc.metadata.get("page"),
            "chunk_index": doc.metadata.get("chunk_index"),
        }
        # Remove None values
        source_info = {k: v for k, v in source_info.items() if v is not None}
        sources.append(source_info)
    
    return sources


class RAGChain:
    """RAG chain for cultural studies Q&A."""
    
    def __init__(self, k: int = 4, temperature: float = 0.7):
        """Initialize RAG chain.
        
        Args:
            k: Number of documents to retrieve
            temperature: LLM temperature
        """
        self.retriever = get_retriever(k=k)
        self.llm = get_llm(temperature=temperature)
        self.prompt = get_qa_prompt()
    
    def invoke(self, question: str) -> Dict[str, Any]:
        """Process a question through the RAG pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer and sources
        """
        # Retrieve relevant documents
        docs = self.retriever.retrieve(question)
        
        # Format context
        context = format_docs(docs)
        
        # Generate answer
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        return {
            "answer": answer,
            "sources": extract_sources(docs),
            "context_used": len(docs)
        }
    
    def invoke_with_scores(self, question: str) -> Dict[str, Any]:
        """Process question and include relevance scores.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer, sources, and scores
        """
        # Retrieve with scores
        docs_with_scores = self.retriever.retrieve_with_scores(question)
        docs = [doc for doc, _ in docs_with_scores]
        scores = [score for _, score in docs_with_scores]
        
        # Format context
        context = format_docs(docs)
        
        # Generate answer
        chain = self.prompt | self.llm | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        # Combine sources with scores
        sources = extract_sources(docs)
        for i, source in enumerate(sources):
            source["relevance_score"] = float(scores[i]) if i < len(scores) else None
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(docs)
        }


class AnalysisChain:
    """Chain for in-depth cultural/literary analysis."""
    
    def __init__(self, k: int = 6):
        """Initialize analysis chain with more context."""
        self.retriever = get_retriever(k=k)
        self.llm = get_llm(temperature=0.5)
        self.prompt = get_analysis_prompt()
    
    def analyze(self, topic: str) -> Dict[str, Any]:
        """Perform analysis on a topic.
        
        Args:
            topic: Topic to analyze
            
        Returns:
            Analysis result with sources
        """
        docs = self.retriever.retrieve(topic)
        context = format_docs(docs)
        
        chain = self.prompt | self.llm | StrOutputParser()
        analysis = chain.invoke({
            "context": context,
            "topic": topic
        })
        
        return {
            "analysis": analysis,
            "sources": extract_sources(docs)
        }


class LinguisticChain:
    """Chain for linguistic analysis questions."""
    
    def __init__(self, k: int = 4):
        """Initialize linguistic chain."""
        self.retriever = get_retriever(k=k)
        self.llm = get_llm(temperature=0.3)
        self.prompt = get_linguistic_prompt()
    
    def analyze(self, question: str) -> Dict[str, Any]:
        """Perform linguistic analysis.
        
        Args:
            question: Linguistic question
            
        Returns:
            Analysis result with sources
        """
        docs = self.retriever.retrieve(question)
        context = format_docs(docs)
        
        chain = self.prompt | self.llm | StrOutputParser()
        analysis = chain.invoke({
            "context": context,
            "question": question
        })
        
        return {
            "analysis": analysis,
            "sources": extract_sources(docs)
        }


def get_rag_chain(k: int = 4, temperature: float = 0.7) -> RAGChain:
    """Factory function for RAG chain.
    
    Args:
        k: Number of documents to retrieve
        temperature: LLM temperature
        
    Returns:
        RAGChain instance
    """
    return RAGChain(k=k, temperature=temperature)


def get_analysis_chain(k: int = 6) -> AnalysisChain:
    """Factory function for analysis chain."""
    return AnalysisChain(k=k)


def get_linguistic_chain(k: int = 4) -> LinguisticChain:
    """Factory function for linguistic chain."""
    return LinguisticChain(k=k)
