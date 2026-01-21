"""Metadata management and enrichment for Cultural Nodes.

This module defines the complete metadata schema and provides functions
for validation, enrichment, and merging of metadata from different sources
(curatorial, discourse, user-provided).
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json


class CulturalMetadata(BaseModel):
    """Complete metadata schema for culturally-aware knowledge.
    
    This combines curatorial metadata (source, authority, origin),
    discourse metadata (role, position, themes), and technical metadata
    (embedding version, timestamps).
    """
    
    # Required fields
    title: str = Field(..., description="Document or chunk title")
    source_type: str = Field(..., description="Source type (community/academic/media/archival)")
    authority_level: str = Field(..., description="Authority level of source")
    epistemic_origin: str = Field(..., description="Origin of knowledge")
    
    # Discourse fields
    themes: List[str] = Field(default_factory=list, description="Thematic tags")
    discourse_position: str = Field(default="neutral", description="Discourse stance")
    chunk_role: str = Field(default="unknown", description="Role in discourse")
    
    # Cultural context
    language: str = Field(default="id", description="Primary language")
    region: str = Field(default="nusantara", description="Cultural/geographic region")
    
    # Sensitivity and policy
    sensitivity: str = Field(default="standard", description="Content sensitivity level")
    ingest_policy: str = Field(default="cultural", description="Ingestion policy applied")
    
    # Optional enrichment
    related_nodes: List[str] = Field(default_factory=list, description="Related document IDs")
    has_citation: bool = Field(default=False, description="Contains citations")
    
    # Technical metadata
    embedding_version: Optional[str] = Field(None, description="Embedding model version")
    embedding_model: Optional[str] = Field(None, description="Embedding model name")
    
    # System fields
    folder_path: Optional[str] = Field(None, description="Source folder path")
    filename: Optional[str] = Field(None, description="Original filename")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")
    ingested_at: Optional[str] = Field(None, description="Ingestion timestamp")
    
    @validator('themes', pre=True)
    def parse_themes(cls, v):
        """Parse themes if they come as string."""
        if isinstance(v, str):
            return [t.strip() for t in v.split(',') if t.strip()]
        return v
    
    class Config:
        extra = 'allow'  # Allow additional fields


class MetadataEnricher:
    """Enriches and validates metadata from multiple sources."""
    
    SENSITIVITY_KEYWORDS = {
        "high": [
            "konflik", "kekerasan", "diskriminasi", "violence", "discrimination",
            "politik", "political", "kontroversial", "controversial"
        ],
        "medium": [
            "kritik", "debat", "critique", "debate", "polemik"
        ]
    }
    
    def __init__(self):
        """Initialize metadata enricher."""
        pass
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate metadata against schema.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Attempt to create CulturalMetadata model
            # This will validate all fields and types
            CulturalMetadata(**metadata)
            return True
        except Exception as e:
            raise ValueError(f"Metadata validation failed: {str(e)}")
    
    def infer_sensitivity(self, content: str, metadata: Dict) -> str:
        """Infer content sensitivity level.
        
        Args:
            content: Text content to analyze
            metadata: Existing metadata
            
        Returns:
            Sensitivity level: 'high', 'medium', or 'standard'
        """
        content_lower = content.lower()
        
        # Check for high sensitivity keywords
        high_matches = sum(
            1 for keyword in self.SENSITIVITY_KEYWORDS["high"]
            if keyword in content_lower
        )
        
        if high_matches >= 2:
            return "high"
        
        # Check for medium sensitivity keywords
        medium_matches = sum(
            1 for keyword in self.SENSITIVITY_KEYWORDS["medium"]
            if keyword in content_lower
        )
        
        if medium_matches >= 2:
            return "medium"
        
        # Default
        return "standard"
    
    def enrich_metadata(
        self,
        base_metadata: Dict,
        curatorial_metadata: Optional[Dict] = None,
        discourse_metadata: Optional[Dict] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Combine metadata from all sources.
        
        Args:
            base_metadata: Base metadata (from document loader)
            curatorial_metadata: Metadata from curatorial gate
            discourse_metadata: Metadata from discourse chunker
            content: Optional content for analysis
            
        Returns:
            Enriched metadata dictionary
        """
        # Start with base
        enriched = base_metadata.copy()
        
        # Merge curatorial metadata
        if curatorial_metadata:
            enriched.update(curatorial_metadata)
        
        # Merge discourse metadata
        if discourse_metadata:
            enriched.update(discourse_metadata)
        
        # Infer sensitivity if content provided
        if content and 'sensitivity' not in enriched:
            enriched['sensitivity'] = self.infer_sensitivity(content, enriched)
        
        # Add timestamp if not present
        if 'ingested_at' not in enriched:
            enriched['ingested_at'] = datetime.utcnow().isoformat()
        
        # Ensure required fields have defaults
        defaults = {
            'themes': [],
            'related_nodes': [],
            'discourse_position': 'neutral',
            'chunk_role': 'unknown',
            'language': 'id',
            'region': 'nusantara',
            'sensitivity': 'standard',
            'ingest_policy': 'cultural',
            'has_citation': False,
        }
        
        for key, default_value in defaults.items():
            if key not in enriched:
                enriched[key] = default_value
        
        return enriched
    
    def add_relations(
        self,
        metadata: Dict,
        related_ids: List[str]
    ) -> Dict:
        """Add related node IDs to metadata.
        
        Args:
            metadata: Metadata to update
            related_ids: List of related document/chunk IDs
            
        Returns:
            Updated metadata
        """
        if 'related_nodes' not in metadata:
            metadata['related_nodes'] = []
        
        # Add new relations, avoiding duplicates
        for node_id in related_ids:
            if node_id not in metadata['related_nodes']:
                metadata['related_nodes'].append(node_id)
        
        return metadata
    
    def to_storage_format(self, metadata: Dict) -> Dict:
        """Convert metadata to storage-friendly format.
        
        Serializes complex types (lists, dates) for storage.
        
        Args:
            metadata: Metadata to convert
            
        Returns:
            Storage-ready metadata
        """
        storage_meta = metadata.copy()
        
        # Convert lists to JSON strings for storage
        for key in ['themes', 'related_nodes']:
            if key in storage_meta and isinstance(storage_meta[key], list):
                storage_meta[key] = json.dumps(storage_meta[key])
        
        return storage_meta
    
    def from_storage_format(self, metadata: Dict) -> Dict:
        """Convert metadata from storage format back to usable format.
        
        Args:
            metadata: Metadata from storage
            
        Returns:
            Usable metadata with proper types
        """
        usable_meta = metadata.copy()
        
        # Parse JSON strings back to lists
        for key in ['themes', 'related_nodes']:
            if key in usable_meta and isinstance(usable_meta[key], str):
                try:
                    usable_meta[key] = json.loads(usable_meta[key])
                except:
                    usable_meta[key] = []
        
        return usable_meta


def merge_metadata(
    base: Dict,
    curatorial: Optional[Dict] = None,
    discourse: Optional[Dict] = None
) -> Dict:
    """Convenience function to merge metadata from multiple sources.
    
    Args:
        base: Base metadata
        curatorial: Curatorial gate metadata
        discourse: Discourse chunker metadata
        
    Returns:
        Merged metadata
    """
    enricher = MetadataEnricher()
    return enricher.enrich_metadata(base, curatorial, discourse)


def get_metadata_enricher() -> MetadataEnricher:
    """Factory function to get metadata enricher.
    
    Returns:
        MetadataEnricher instance
    """
    return MetadataEnricher()
