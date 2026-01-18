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
    Ingest raw text into the knowledge base.
    """
    try:
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
    category: str = Form(default="general")
):
    """
    Upload and ingest a file (PDF, MD, or TXT) into the knowledge base.
    """
    # Validate file extension
    allowed_extensions = [".pdf", ".md", ".markdown", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Ingest the file
        pipeline = get_pipeline(verbose=False)
        chunks = pipeline.ingest_file(tmp_path, category=category)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "message": f"Ingested {chunks} chunks",
            "filename": file.filename
        }
    except Exception as e:
        # Clean up on error
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
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
