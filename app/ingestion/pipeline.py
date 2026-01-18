"""Document ingestion pipeline."""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.loaders import load_directory, load_url, load_pdf, load_text, load_markdown
from app.ingestion.chunker import chunk_documents
from app.core.vectorstore import add_documents, get_collection_stats


class IngestionPipeline:
    """Pipeline for ingesting documents into the knowledge base."""
    
    def __init__(self, verbose: bool = True):
        """Initialize pipeline.
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
    
    def _log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def ingest_file(self, file_path: str, category: str = "general") -> int:
        """Ingest a single file into the knowledge base.
        
        Args:
            file_path: Path to the file
            category: Category tag for the document
            
        Returns:
            Number of chunks ingested
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        self._log(f"[LOAD] Loading: {path.name}")
        
        # Load based on extension
        if ext == ".pdf":
            documents = load_pdf(file_path)
        elif ext in [".md", ".markdown"]:
            documents = load_markdown(file_path)
        elif ext == ".txt":
            documents = load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        # Add category metadata
        for doc in documents:
            doc.metadata["category"] = category
        
        # Chunk documents
        self._log(f"[CHUNK] Chunking: {len(documents)} document(s)")
        chunks = chunk_documents(documents)
        
        # Add to vector store
        self._log(f"[STORE] Storing: {len(chunks)} chunk(s)")
        add_documents(chunks)
        
        self._log(f"[DONE] Complete: {path.name}")
        return len(chunks)
    
    def ingest_directory(
        self,
        directory_path: str,
        category: str = "general",
        recursive: bool = True,
        extensions: Optional[List[str]] = None
    ) -> int:
        """Ingest all documents from a directory.
        
        Args:
            directory_path: Path to directory
            category: Category tag for all documents
            recursive: Whether to search subdirectories
            extensions: File extensions to include
            
        Returns:
            Total number of chunks ingested
        """
        self._log(f"[SCAN] Scanning directory: {directory_path}")
        
        # Load all documents
        documents = load_directory(directory_path, recursive, extensions)
        
        if not documents:
            self._log("[WARN] No documents found")
            return 0
        
        # Add category metadata
        for doc in documents:
            doc.metadata["category"] = category
        
        # Chunk documents
        self._log(f"[CHUNK] Chunking: {len(documents)} document(s)")
        chunks = chunk_documents(documents)
        
        # Add to vector store
        self._log(f"[STORE] Storing: {len(chunks)} chunk(s)")
        add_documents(chunks)
        
        self._log(f"[DONE] Complete: {len(chunks)} chunks from {len(documents)} documents")
        return len(chunks)
    
    def ingest_url(self, url: str, category: str = "web") -> int:
        """Ingest content from a URL.
        
        Args:
            url: Web URL to scrape
            category: Category tag for the content
            
        Returns:
            Number of chunks ingested
        """
        self._log(f"[FETCH] Fetching: {url}")
        
        documents = load_url(url)
        
        # Add category metadata
        for doc in documents:
            doc.metadata["category"] = category
        
        # Chunk documents
        self._log(f"[CHUNK] Chunking: {len(documents)} document(s)")
        chunks = chunk_documents(documents)
        
        # Add to vector store
        self._log(f"[STORE] Storing: {len(chunks)} chunk(s)")
        add_documents(chunks)
        
        self._log(f"[DONE] Complete: {url}")
        return len(chunks)
    
    def ingest_text(
        self,
        text: str,
        title: str = "untitled",
        category: str = "general"
    ) -> int:
        """Ingest raw text into the knowledge base.
        
        Args:
            text: Raw text content
            title: Title for the content
            category: Category tag
            
        Returns:
            Number of chunks ingested
        """
        self._log(f"[PROCESS] Processing: {title}")
        
        from app.ingestion.chunker import chunk_text
        
        chunks = chunk_text(text, metadata={
            "title": title,
            "category": category,
            "source_type": "text"
        })
        
        self._log(f"[STORE] Storing: {len(chunks)} chunk(s)")
        add_documents(chunks)
        
        self._log(f"[DONE] Complete: {title}")
        return len(chunks)
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary with collection stats
        """
        return get_collection_stats()


def get_pipeline(verbose: bool = True) -> IngestionPipeline:
    """Factory function to get pipeline instance.
    
    Args:
        verbose: Whether to print progress messages
        
    Returns:
        IngestionPipeline instance
    """
    return IngestionPipeline(verbose=verbose)
