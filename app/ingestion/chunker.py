"""Text chunking strategies for document processing."""

from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Get configured text splitter.
    
    Returns:
        RecursiveCharacterTextSplitter with optimal settings for cultural texts
    """
    settings = get_settings()
    
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
        separators=[
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            ", ",    # Clauses
            " ",     # Words
            "",      # Characters
        ]
    )


def chunk_documents(documents: List[Document]) -> List[Document]:
    """Split documents into smaller chunks.
    
    Args:
        documents: List of documents to chunk
        
    Returns:
        List of chunked documents with preserved metadata
    """
    splitter = get_text_splitter()
    chunks = splitter.split_documents(documents)
    
    # Add chunk index to metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    
    return chunks


def chunk_text(text: str, metadata: dict = None) -> List[Document]:
    """Chunk raw text into documents.
    
    Args:
        text: Raw text to chunk
        metadata: Optional metadata to attach
        
    Returns:
        List of Document objects
    """
    splitter = get_text_splitter()
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[metadata or {}]
    )
    
    # Add chunk indices
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    
    return chunks
