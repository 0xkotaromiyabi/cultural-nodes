"""Curatorial gate for culturally-aware document ingestion.

This module implements the first layer of epistemic awareness by extracting
metadata about knowledge provenance, authority level, and cultural context
from the file path and content before documents enter the RAG pipeline.
"""

from pathlib import Path
from typing import Dict, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import re


class AuthorityLevel(str, Enum):
    """Authority level of knowledge source."""
    SITUATED = "situated"  # Local, community knowledge
    ACADEMIC = "academic"  # Peer-reviewed, scholarly
    INSTITUTIONAL = "institutional"  # Official, governmental
    MEDIA = "media"  # Journalistic, commentary
    ARCHIVAL = "archival"  # Historical documents


class EpistemicOrigin(str, Enum):
    """Epistemic origin of knowledge."""
    LOCAL_KNOWLEDGE = "local_knowledge"
    COMMUNITY_ARCHIVE = "community_archive"
    ACADEMIC_RESEARCH = "academic_research"
    INSTITUTIONAL_RECORD = "institutional_record"
    MEDIA_DISCOURSE = "media_discourse"
    HISTORICAL_ARCHIVE = "historical_archive"


class CuratorialMetadata(BaseModel):
    """Metadata from curatorial gate."""
    source_type: str = Field(..., description="Type of source (community/academic/media/archival)")
    authority_level: AuthorityLevel = Field(..., description="Authority level of source")
    epistemic_origin: EpistemicOrigin = Field(..., description="Origin of knowledge")
    language: str = Field(default="id", description="Primary language (id/en)")
    region: str = Field(default="nusantara", description="Geographic/cultural region")
    ingest_policy: str = Field(default="cultural", description="Ingestion policy applied")
    folder_path: str = Field(..., description="Relative folder path from knowledge_base")
    

class CuratorialGate:
    """Main curatorial gate logic.
    
    Extracts epistemic metadata from file paths and content to ensure
    culturally-aware ingestion that respects knowledge provenance.
    """
    
    # Mapping from folder structure to source metadata
    SOURCE_TYPE_MAP = {
        "community": {
            "authority_level": AuthorityLevel.SITUATED,
            "epistemic_origin": EpistemicOrigin.COMMUNITY_ARCHIVE,
        },
        "academic": {
            "authority_level": AuthorityLevel.ACADEMIC,
            "epistemic_origin": EpistemicOrigin.ACADEMIC_RESEARCH,
        },
        "media": {
            "authority_level": AuthorityLevel.MEDIA,
            "epistemic_origin": EpistemicOrigin.MEDIA_DISCOURSE,
        },
        "archival": {
            "authority_level": AuthorityLevel.ARCHIVAL,
            "epistemic_origin": EpistemicOrigin.HISTORICAL_ARCHIVE,
        },
    }
    
    # Language detection patterns (simple heuristic)
    INDONESIAN_PATTERNS = [
        r'\byang\b', r'\bdan\b', r'\bdi\b', r'\bke\b', r'\bdari\b',
        r'\bdengan\b', r'\buntuk\b', r'\bpada\b', r'\badalah\b'
    ]
    
    def __init__(self, knowledge_base_root: str = "./knowledge_base"):
        """Initialize curatorial gate.
        
        Args:
            knowledge_base_root: Root path of knowledge base
        """
        self.knowledge_base_root = Path(knowledge_base_root)
    
    def extract_source_type(self, file_path: str) -> str:
        """Extract source type from folder structure.
        
        Args:
            file_path: Full path to file
            
        Returns:
            Source type string (community/academic/media/archival/general)
        """
        path = Path(file_path)
        
        # Get relative path from knowledge_base root
        try:
            rel_path = path.relative_to(self.knowledge_base_root)
            parts = rel_path.parts
            
            # First folder indicates source type
            if len(parts) > 0:
                first_folder = parts[0]
                if first_folder in self.SOURCE_TYPE_MAP:
                    return first_folder
        except ValueError:
            # Path is not relative to knowledge_base_root
            pass
        
        # Fallback: check for old structure (pdf/text/markdown)
        if 'pdf' in str(path) or 'text' in str(path) or 'markdown' in str(path):
            return "general"  # Legacy format-based organization
        
        return "general"
    
    def determine_authority_level(self, source_type: str) -> AuthorityLevel:
        """Map source type to authority level.
        
        Args:
            source_type: Source type from folder structure
            
        Returns:
            Authority level enum
        """
        if source_type in self.SOURCE_TYPE_MAP:
            return self.SOURCE_TYPE_MAP[source_type]["authority_level"]
        return AuthorityLevel.SITUATED  # Default to situated knowledge
    
    def determine_epistemic_origin(self, source_type: str) -> EpistemicOrigin:
        """Map source type to epistemic origin.
        
        Args:
            source_type: Source type from folder structure
            
        Returns:
            Epistemic origin enum
        """
        if source_type in self.SOURCE_TYPE_MAP:
            return self.SOURCE_TYPE_MAP[source_type]["epistemic_origin"]
        return EpistemicOrigin.LOCAL_KNOWLEDGE  # Default
    
    def detect_language(self, text: str, sample_size: int = 500) -> str:
        """Detect primary language using simple heuristics.
        
        Args:
            text: Text content to analyze
            sample_size: Number of characters to sample
            
        Returns:
            Language code: 'id' for Indonesian, 'en' for English
        """
        # Sample beginning of text
        sample = text[:sample_size].lower()
        
        # Count Indonesian pattern matches
        indonesian_matches = sum(
            1 for pattern in self.INDONESIAN_PATTERNS
            if re.search(pattern, sample)
        )
        
        # If 3 or more Indonesian patterns found, classify as Indonesian
        return "id" if indonesian_matches >= 3 else "en"
    
    def extract_region(self, metadata: Dict) -> str:
        """Extract or infer regional/cultural context.
        
        Args:
            metadata: Existing metadata dictionary
            
        Returns:
            Region identifier
        """
        # For now, use simple heuristic
        # Can be extended to parse from metadata or content
        language = metadata.get("language", "id")
        
        if language == "id":
            return "nusantara"
        return "global"
    
    def get_folder_path(self, file_path: str) -> str:
        """Get relative folder path from knowledge_base root.
        
        Args:
            file_path: Full path to file
            
        Returns:
            Relative folder path
        """
        path = Path(file_path)
        try:
            rel_path = path.relative_to(self.knowledge_base_root)
            return str(rel_path.parent)
        except ValueError:
            return str(path.parent)
    
    def apply_curatorial_policy(self, metadata: CuratorialMetadata) -> CuratorialMetadata:
        """Apply cultural ingestion policy based on metadata.
        
        This is where we can add special handling for different source types.
        For example, community sources might get additional context preservation.
        
        Args:
            metadata: Curatorial metadata
            
        Returns:
            Enhanced metadata with policy applied
        """
        # For now, mark all as using 'cultural' policy
        # Can be extended to have different policies per source type
        metadata.ingest_policy = "cultural"
        
        return metadata
    
    def curate_document(
        self, 
        file_path: str,
        content: Optional[str] = None,
        existing_metadata: Optional[Dict] = None
    ) -> CuratorialMetadata:
        """Main curatorial function to enrich document with epistemic metadata.
        
        Args:
            file_path: Path to the file being ingested
            content: Optional text content for language detection
            existing_metadata: Optional existing metadata to merge
            
        Returns:
            CuratorialMetadata with full epistemic context
        """
        # Extract source type from folder structure
        source_type = self.extract_source_type(file_path)
        
        # Determine authority and origin
        authority_level = self.determine_authority_level(source_type)
        epistemic_origin = self.determine_epistemic_origin(source_type)
        
        # Detect language if content provided
        language = "id"  # Default
        if content:
            language = self.detect_language(content)
        elif existing_metadata and "language" in existing_metadata:
            language = existing_metadata["language"]
        
        # Get folder path
        folder_path = self.get_folder_path(file_path)
        
        # Create base metadata
        metadata = CuratorialMetadata(
            source_type=source_type,
            authority_level=authority_level,
            epistemic_origin=epistemic_origin,
            language=language,
            region="",  # Will be set by extract_region
            ingest_policy="cultural",
            folder_path=folder_path
        )
        
        # Extract region
        metadata.region = self.extract_region(metadata.dict())
        
        # Apply curatorial policy
        metadata = self.apply_curatorial_policy(metadata)
        
        return metadata


def get_curator(knowledge_base_root: str = "./knowledge_base") -> CuratorialGate:
    """Factory function to get curator instance.
    
    Args:
        knowledge_base_root: Root path of knowledge base
        
    Returns:
        CuratorialGate instance
    """
    return CuratorialGate(knowledge_base_root=knowledge_base_root)
