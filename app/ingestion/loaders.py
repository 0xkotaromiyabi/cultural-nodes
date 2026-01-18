"""Document loaders for various file formats."""

import os
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    WebBaseLoader,
)


class DocumentLoaderFactory:
    """Factory for creating appropriate document loaders."""
    
    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
    }
    
    @classmethod
    def get_loader(cls, file_path: str):
        """Get appropriate loader for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Appropriate document loader
            
        Raises:
            ValueError: If file type is not supported
        """
        ext = Path(file_path).suffix.lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        file_type = cls.SUPPORTED_EXTENSIONS[ext]
        
        if file_type == "pdf":
            return PyPDFLoader(file_path)
        elif file_type == "text":
            return TextLoader(file_path, encoding="utf-8")
        elif file_type == "markdown":
            return UnstructuredMarkdownLoader(file_path)
        
        raise ValueError(f"No loader for file type: {file_type}")


def load_pdf(file_path: str) -> List[Document]:
    """Load a PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        List of documents (one per page)
    """
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    # Add source metadata
    for doc in documents:
        doc.metadata["source_type"] = "pdf"
        doc.metadata["filename"] = Path(file_path).name
    
    return documents


def load_text(file_path: str) -> List[Document]:
    """Load a text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        List containing one document
    """
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    
    for doc in documents:
        doc.metadata["source_type"] = "text"
        doc.metadata["filename"] = Path(file_path).name
    
    return documents


def load_markdown(file_path: str) -> List[Document]:
    """Load a markdown file.
    
    Args:
        file_path: Path to markdown file
        
    Returns:
        List of documents
    """
    loader = UnstructuredMarkdownLoader(file_path)
    documents = loader.load()
    
    for doc in documents:
        doc.metadata["source_type"] = "markdown"
        doc.metadata["filename"] = Path(file_path).name
    
    return documents


def load_url(url: str) -> List[Document]:
    """Load content from a URL.
    
    Args:
        url: Web URL to scrape
        
    Returns:
        List of documents
    """
    loader = WebBaseLoader(url)
    documents = loader.load()
    
    for doc in documents:
        doc.metadata["source_type"] = "web"
        doc.metadata["url"] = url
    
    return documents


def load_directory(
    directory_path: str,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> List[Document]:
    """Load all supported documents from a directory.
    
    Args:
        directory_path: Path to directory
        recursive: Whether to search subdirectories
        extensions: List of extensions to include (e.g., [".pdf", ".md"])
        
    Returns:
        List of all loaded documents
    """
    documents = []
    path = Path(directory_path)
    
    if extensions is None:
        extensions = list(DocumentLoaderFactory.SUPPORTED_EXTENSIONS.keys())
    
    # Normalize extensions
    extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]
    
    # Find all matching files
    pattern = "**/*" if recursive else "*"
    
    for file_path in path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            try:
                loader = DocumentLoaderFactory.get_loader(str(file_path))
                docs = loader.load()
                
                # Add metadata
                for doc in docs:
                    doc.metadata["source_type"] = DocumentLoaderFactory.SUPPORTED_EXTENSIONS.get(
                        file_path.suffix.lower(), "unknown"
                    )
                    doc.metadata["filename"] = file_path.name
                    doc.metadata["filepath"] = str(file_path)
                
                documents.extend(docs)
                print(f"[OK] Loaded: {file_path.name} ({len(docs)} chunks)")
                
            except Exception as e:
                print(f"[ERROR] Error loading {file_path}: {e}")
    
    return documents
