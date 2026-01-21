"""API routes for Cultural AI RAG system."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile
import os

from app.core.rag_chain import get_rag_chain, get_analysis_chain, get_linguistic_chain
from app.core.vectorstore import get_collection_stats, similarity_search
from app.ingestion.pipeline import get_pipeline


router = APIRouter(prefix="/api", tags=["Cultural AI"])


# ============== Request/Response Models ==============

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., description="User's question", min_length=1)
    k: int = Field(default=4, description="Number of documents to retrieve", ge=1, le=10)
    temperature: float = Field(default=0.7, description="LLM temperature", ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: List[dict]
    context_used: int


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""
    topic: str = Field(..., description="Topic to analyze", min_length=1)
    analysis_type: str = Field(
        default="cultural",
        description="Type of analysis: cultural or linguistic"
    )


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint."""
    analysis: str
    sources: List[dict]


class IngestTextRequest(BaseModel):
    """Request model for text ingestion."""
    text: str = Field(..., description="Text content to ingest", min_length=10)
    title: str = Field(default="untitled", description="Title for the content")
    category: str = Field(default="general", description="Category tag")
    source_type: str = Field(default="general", description="Source type: community/academic/media/archival")


class IngestURLRequest(BaseModel):
    """Request model for URL ingestion."""
    url: str = Field(..., description="URL to ingest")
    category: str = Field(default="web", description="Category tag")


class SearchRequest(BaseModel):
    """Request model for similarity search."""
    query: str = Field(..., description="Search query")
    k: int = Field(default=5, description="Number of results", ge=1, le=20)


class StatsResponse(BaseModel):
    """Response model for stats endpoint."""
    name: str
    count: int


class IngestDirectoryRequest(BaseModel):
    """Request model for directory ingestion."""
    directory_path: str = Field(..., description="Path to directory")
    source_type: str = Field(default="general", description="Source type: community/academic/media/archival")
    category: str = Field(default="general", description="Category tag")
    recursive: bool = Field(default=True, description="Search subdirectories")


# ============== Chat Endpoints ==============

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a question and get an AI-generated answer based on the knowledge base.
    
    The system retrieves relevant documents and uses them as context for the LLM.
    """
    try:
        chain = get_rag_chain(k=request.k, temperature=request.temperature)
        result = chain.invoke(request.question)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    Perform in-depth analysis on a cultural or linguistic topic.
    """
    try:
        if request.analysis_type == "linguistic":
            chain = get_linguistic_chain()
        else:
            chain = get_analysis_chain()
        
        result = chain.analyze(request.topic)
        return AnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Ingestion Endpoints ==============

@router.post("/ingest/text")
async def ingest_text(request: IngestTextRequest):
    """
    Ingest raw text into the knowledge base with source type categorization.
    """
    try:
        # Save text to appropriate folder if source_type is specified
        if request.source_type in ["community", "academic", "media", "archival"]:
            # Determine target directory
            if request.source_type == "community":
                target_dir = "./knowledge_base/community/manifesto"
            else:
                target_dir = f"./knowledge_base/{request.source_type}"
            
            os.makedirs(target_dir, exist_ok=True)
            
            # Save as text file
            filename = f"{request.title.replace(' ', '-').lower()}.txt"
            target_path = os.path.join(target_dir, filename)
            
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(request.text)
            
            # Ingest from file
            pipeline = get_pipeline(verbose=False)
            chunks = pipeline.ingest_file(target_path, category=request.category)
            
            return {
                "status": "success",
                "message": f"Ingested {chunks} chunks",
                "title": request.title,
                "source_type": request.source_type,
                "saved_to": target_path
            }
        else:
            # Original behavior for general text
            pipeline = get_pipeline(verbose=False)
            chunks = pipeline.ingest_text(
                text=request.text,
                title=request.title,
                category=request.category
            )
            return {
                "status": "success",
                "message": f"Ingested {chunks} chunks",
                "title": request.title
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/url")
async def ingest_url(request: IngestURLRequest):
    """
    Ingest content from a web URL into the knowledge base.
    """
    try:
        pipeline = get_pipeline(verbose=False)
        chunks = pipeline.ingest_url(url=request.url, category=request.category)
        return {
            "status": "success",
            "message": f"Ingested {chunks} chunks from URL",
            "url": request.url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    source_type: str = Form(default="general", description="Source type: community/academic/media/archival"),
    category: str = Form(default="general")
):
    """
    Upload and ingest a file into the knowledge base with source type categorization.
    
    The file will be saved to the appropriate knowledge_base subfolder based on source_type.
    """
    # Validate file extension
    allowed_extensions = [".pdf", ".md", ".markdown", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    # Validate source type
    valid_source_types = ["community", "academic", "media", "archival", "general"]
    if source_type not in valid_source_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type. Allowed: {valid_source_types}"
        )
    
    try:
        # Determine target directory based on source type
        if source_type in ["community", "academic", "media", "archival"]:
            # For community, use subdirectory based on file type
            if source_type == "community":
                # Default to transcript for community uploads
                target_dir = f"./knowledge_base/community/transcript"
            else:
                target_dir = f"./knowledge_base/{source_type}"
        else:
            # General category - use temp
            target_dir = "./knowledge_base/general"
        
        # Create directory if not exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Save file to knowledge base
        target_path = os.path.join(target_dir, file.filename)
        
        # Read file content
        content = await file.read()
        
        # Write to target location
        with open(target_path, 'wb') as f:
            f.write(content)
        
        # Ingest the file from its permanent location
        pipeline = get_pipeline(verbose=False)
        chunks = pipeline.ingest_file(target_path, category=category)
        
        return {
            "status": "success",
            "message": f"Ingested {chunks} chunks",
            "filename": file.filename,
            "source_type": source_type,
            "saved_to": target_path
        }
    except Exception as e:
        # Clean up on error if file was created
        if 'target_path' in locals() and os.path.exists(target_path):
            os.unlink(target_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/directory")
async def ingest_directory(request: IngestDirectoryRequest):
    """
    Ingest all files from a directory with source type categorization.
    
    Useful for batch importing documents into specific categories.
    """
    try:
        if not os.path.exists(request.directory_path):
            raise HTTPException(status_code=404, detail="Directory not found")
        
        if not os.path.isdir(request.directory_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        pipeline = get_pipeline(verbose=False)
        chunks = pipeline.ingest_directory(
            directory_path=request.directory_path,
            category=request.category,
            recursive=request.recursive
        )
        
        return {
            "status": "success",
            "message": f"Ingested {chunks} total chunks from directory",
            "directory": request.directory_path,
            "source_type": request.source_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Search & Stats Endpoints ==============

@router.post("/search")
async def search(request: SearchRequest):
    """
    Perform similarity search on the knowledge base.
    """
    try:
        docs = similarity_search(request.query, k=request.k)
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata
            })
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get statistics about the knowledge base.
    """
    try:
        stats = get_collection_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "Cultural AI RAG"}


# ============== Cultural Search Endpoints (NEW) ==============

class CulturalChatRequest(BaseModel):
    """Request for cultural chat."""
    question: str = Field(..., min_length=1)
    strategy: str = Field(default="authority_ranked", description="Retrieval strategy")
    boost_community: bool = Field(default=True, description="Boost community sources")
    k: int = Field(default=4, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class CulturalPluralRequest(BaseModel):
    """Request for plural perspectives retrieval."""
    question: str = Field(..., min_length=1)
    k_per_source: int = Field(default=2, ge=1, le=5)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class CulturalFilterRequest(BaseModel):
    """Request for epistemic filtering."""
    question: str = Field(..., min_length=1)
    source_type: Optional[str] = Field(None, description="Filter by source: community/academic/media")
    authority_level: Optional[str] = Field(None, description="Filter by authority: situated/academic/institutional")
    k: int = Field(default=4, ge=1, le=10)


class CulturalSearchRequest(BaseModel):
    """Request for cultural search with metadata."""
    query: str = Field(..., min_length=1)
    source_type: Optional[str] = None
    authority_level: Optional[str] = None
    themes: Optional[List[str]] = None
    k: int = Field(default=5, ge=1, le=20)


@router.post("/cultural/chat")
async def cultural_chat(request: CulturalChatRequest):
    """
    Cultural RAG with epistemic awareness and retrieval strategy selection.
    
    Strategies:
    - standard: Regular similarity search
    - epistemic: Filter by source/authority
    - plural: Multiple perspectives
    - authority_ranked: Boost community knowledge
    - discourse_balanced: Balance critical/supportive positions
    """
    try:
        from app.core.cultural_rag_chain import get_cultural_rag_chain
        from app.core.cultural_retriever import RetrievalStrategy
        
        chain = get_cultural_rag_chain(
            k=request.k,
            temperature=request.temperature,
            boost_community=request.boost_community
        )
        
        # Map string to enum
        strategy_map = {
            "standard": RetrievalStrategy.STANDARD,
            "epistemic": RetrievalStrategy.EPISTEMIC,
            "plural": RetrievalStrategy.PLURAL,
            "authority_ranked": RetrievalStrategy.AUTHORITY_RANKED,
            "discourse_balanced": RetrievalStrategy.DISCOURSE_BALANCED
        }
        
        strategy = strategy_map.get(request.strategy, RetrievalStrategy.AUTHORITY_RANKED)
        
        result = chain.invoke(
            question=request.question,
            strategy=strategy,
            k=request.k,
            boost_community=request.boost_community
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cultural/plural")
async def cultural_plural(request: CulturalPluralRequest):
    """
    Get answer with plural perspectives from different knowledge sources.
    
    Returns perspectives from:
    - Community knowledge (situated)
    - Academic research
    - Media discourse
    - Archival sources
    """
    try:
        from app.core.cultural_rag_chain import get_cultural_rag_chain
        
        chain = get_cultural_rag_chain(temperature=request.temperature)
        result = chain.invoke_plural(
            question=request.question,
            k_per_source=request.k_per_source
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cultural/filters")
async def cultural_filters(request: CulturalFilterRequest):
    """
    Get answer filtered by epistemic criteria.
    
    Filter by:
    - source_type: community, academic, media, archival
    - authority_level: situated, academic, institutional, media, archival
    """
    try:
        from app.core.cultural_rag_chain import get_cultural_rag_chain
        
        chain = get_cultural_rag_chain(k=request.k)
        result = chain.invoke_epistemic(
            question=request.question,
            source_type=request.source_type,
            authority_level=request.authority_level,
            k=request.k
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cultural/search")
async def cultural_search(request: CulturalSearchRequest):
    """
    Search with cultural metadata filtering.
    
    Returns documents with full cultural metadata including:
    - Epistemic origin
    - Authority level
    - Discourse position
    - Themes
    - Citation status
    """
    try:
        from app.core.knowledge_store import get_knowledge_store
        
        knowledge_store = get_knowledge_store()
        
        # Get filtered vector IDs from knowledge store
        vector_ids = knowledge_store.query_by_filters(
            source_type=request.source_type,
            authority_level=request.authority_level,
            themes=request.themes,
            limit=request.k
        )
        
        # Retrieve documents by vector IDs
        results = []
        for vector_id in vector_ids:
            doc_meta = knowledge_store.get_document_by_vector_id(vector_id)
            if doc_meta:
                results.append({
                    "vector_id": vector_id,
                    "title": doc_meta.get("title"),
                    "source_type": doc_meta.get("source_type"),
                    "authority_level": doc_meta.get("authority_level"),
                    "epistemic_origin": doc_meta.get("epistemic_origin"),
                    "discourse_position": doc_meta.get("discourse_position"),
                    "chunk_role": doc_meta.get("chunk_role"),
                    "themes": doc_meta.get("themes", []),
                    "language": doc_meta.get("language"),
                    "has_citation": bool(doc_meta.get("has_citation")),
                })
        
        return {
            "results": results,
            "count": len(results),
            "filters_applied": {
                "source_type": request.source_type,
                "authority_level": request.authority_level,
                "themes": request.themes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
