"""Embedding version tracking for Cultural Nodes.

This module tracks embedding model versions to support co-existence
of multiple embedding versions in the knowledge base, enabling
audit trails and gradual migration to new models.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EmbeddingVersion(BaseModel):
    """Metadata about embedding model version."""
    
    model_name: str = Field(..., description="Model identifier (e.g., 'nomic-embed-text')")
    version: str = Field(..., description="Version identifier (e.g., '2026-01')")
    language_scope: list[str] = Field(default_factory=list, description="Supported languages")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    dimension: Optional[int] = Field(None, description="Embedding dimension")
    
    def to_string(self) -> str:
        """Get version as compact string.
        
        Returns:
            Version string like 'nomic-embed-text:2026-01'
        """
        return f"{self.model_name}:{self.version}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "model_name": self.model_name,
            "version": self.version,
            "language_scope": self.language_scope,
            "created_at": self.created_at,
            "dimension": self.dimension,
        }


class EmbeddingVersionTracker:
    """Tracks and manages embedding versions."""
    
    def __init__(self, model_name: str = "nomic-embed-text"):
        """Initialize version tracker.
        
        Args:
            model_name: Default embedding model name
        """
        self.model_name = model_name
        self.current_version = self._generate_version()
    
    def _generate_version(self) -> str:
        """Generate version identifier from current date.
        
        Returns:
            Version string like '2026-01'
        """
        now = datetime.utcnow()
        return f"{now.year}-{now.month:02d}"
    
    def get_current_version(
        self,
        language_scope: Optional[list[str]] = None,
        dimension: Optional[int] = None
    ) -> EmbeddingVersion:
        """Get current embedding version metadata.
        
        Args:
            language_scope: Languages supported by this embedding
            dimension: Embedding dimension
            
        Returns:
            EmbeddingVersion object
        """
        if language_scope is None:
            language_scope = ["id", "en"]  # Default for nomic-embed-text
        
        return EmbeddingVersion(
            model_name=self.model_name,
            version=self.current_version,
            language_scope=language_scope,
            dimension=dimension,
        )
    
    def create_version_metadata(
        self,
        doc_id: str,
        embedding_version: Optional[EmbeddingVersion] = None
    ) -> Dict:
        """Create metadata to attach to a document.
        
        Args:
            doc_id: Document/chunk ID
            embedding_version: Optional specific version, uses current if not provided
            
        Returns:
            Metadata dictionary
        """
        if embedding_version is None:
            embedding_version = self.get_current_version()
        
        return {
            "doc_id": doc_id,
            "embedding_model": embedding_version.model_name,
            "embedding_version": embedding_version.version,
            "embedding_created_at": embedding_version.created_at,
        }
    
    def supports_coexistence(
        self,
        old_version: EmbeddingVersion,
        new_version: EmbeddingVersion
    ) -> bool:
        """Check if two embedding versions can coexist.
        
        For now, always returns True to allow multiple versions.
        In production, you might check dimension compatibility, etc.
        
        Args:
            old_version: Old embedding version
            new_version: New embedding version
            
        Returns:
            True if versions can coexist
        """
        # Could add logic here to check dimension compatibility
        # For now, allow all versions to coexist
        return True
    
    def get_version_from_metadata(self, metadata: Dict) -> Optional[EmbeddingVersion]:
        """Extract embedding version from metadata.
        
        Args:
            metadata: Document metadata
            
        Returns:
            EmbeddingVersion if found, None otherwise
        """
        if "embedding_model" not in metadata or "embedding_version" not in metadata:
            return None
        
        return EmbeddingVersion(
            model_name=metadata["embedding_model"],
            version=metadata["embedding_version"],
            language_scope=metadata.get("language_scope", []),
            created_at=metadata.get("embedding_created_at", ""),
            dimension=metadata.get("embedding_dimension"),
        )


def get_embedding_version_tracker(model_name: Optional[str] = None) -> EmbeddingVersionTracker:
    """Factory function to get version tracker.
    
    Args:
        model_name: Optional custom model name
        
    Returns:
        EmbeddingVersionTracker instance
    """
    from app.config import get_settings
    
    settings = get_settings()
    model_name = model_name or settings.EMBEDDING_MODEL
    
    return EmbeddingVersionTracker(model_name=model_name)


def get_current_embedding_metadata() -> Dict:
    """Get current embedding version as metadata dict.
    
    Returns:
        Metadata dictionary with current version info
    """
    tracker = get_embedding_version_tracker()
    version = tracker.get_current_version()
    
    return {
        "embedding_model": version.model_name,
        "embedding_version": version.version,
        "embedding_created_at": version.created_at,
    }
