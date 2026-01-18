"""FastAPI main application for Cultural AI RAG system."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import router


# Get frontend path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"[START] Cultural AI RAG System starting...")
    print(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"   LLM Model: {settings.LLM_MODEL}")
    print(f"   Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"   ChromaDB: {settings.CHROMA_PERSIST_DIR}")
    print(f"   Frontend: {FRONTEND_DIR}")
    
    yield
    
    # Shutdown
    print("[STOP] Cultural AI RAG System shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Cultural AI RAG",
    description="""
    AI-powered knowledge base for Cultural Studies, Literature, Linguistics, and Language Sciences.
    
    ## Features
    - **Chat**: Ask questions and get AI-generated answers based on your knowledge base
    - **Analysis**: Perform in-depth cultural and linguistic analysis
    - **Ingestion**: Add documents (PDF, Markdown, Text, URLs) to the knowledge base
    - **Search**: Similarity search across all indexed content
    
    ## Powered By
    - **Ollama** with llama3.1 for generation
    - **ChromaDB** for vector storage
    - **LangChain** for orchestration
    """,
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router)


# Mount static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


# Serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend application."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "name": "Cultural AI RAG",
        "version": "1.0.0",
        "description": "AI untuk Cultural Studies, Sastra, Linguistik, dan Ilmu Bahasa",
        "docs": "/docs",
        "frontend": "Frontend not found. Please check the frontend directory."
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

