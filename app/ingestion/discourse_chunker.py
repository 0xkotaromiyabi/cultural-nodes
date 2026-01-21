"""Discourse-aware text chunking for cultural knowledge.

This module implements semantic chunking that understands discourse structure,
argumentative roles, and thematic coherence rather than just splitting by tokens.
Each chunk becomes a unit of meaning with associated metadata.
"""

from typing import List, Dict, Optional, Literal
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
import re

from app.config import get_settings


# Discourse metadata types
ChunkRole = Literal[
    "argument",
    "counter_argument", 
    "definition",
    "example",
    "narrative",
    "question",
    "unknown"
]

DiscoursePosition = Literal[
    "supportive",
    "critical",
    "neutral",
    "questioning"
]


class DiscourseMetadata(BaseModel):
    """Metadata for discourse-aware chunks."""
    chunk_role: ChunkRole = Field(default="unknown", description="Role in discourse")
    discourse_position: DiscoursePosition = Field(default="neutral", description="Stance/position")
    themes: List[str] = Field(default_factory=list, description="Detected themes")
    has_citation: bool = Field(default=False, description="Contains citations/references")
    

class DiscourseAwareChunker:
    """Chunker that understands discourse structure and meaning."""
    
    # Patterns for detecting discourse roles
    ARGUMENT_PATTERNS = [
        r'oleh karena itu', r'maka', r'dengan demikian',
        r'therefore', r'thus', r'consequently'
    ]
    
    COUNTER_PATTERNS = [
        r'namun', r'tetapi', r'akan tetapi', r'sebaliknya',
        r'however', r'but', r'nevertheless', r'on the contrary'
    ]
    
    DEFINITION_PATTERNS = [
        r'adalah', r'merupakan', r'didefinisikan',
        r'is defined as', r'refers to', r'means'
    ]
    
    EXAMPLE_PATTERNS = [
        r'misalnya', r'contohnya', r'sebagai contoh',
        r'for example', r'for instance', r'such as'
    ]
    
    QUESTION_PATTERNS = [
        r'bagaimana', r'mengapa', r'apa', r'siapa', r'kapan', r'dimana',
        r'how', r'why', r'what', r'who', r'when', r'where', r'\?'
    ]
    
    # Patterns for thematic keywords
    THEME_KEYWORDS = {
        "technology": [r'teknologi', r'digital', r'internet', r'technology', r'software'],
        "power": [r'kekuasaan', r'hegemoni', r'dominasi', r'power', r'hegemony'],
        "culture": [r'budaya', r'kultur', r'tradisi', r'culture', r'tradition'],
        "language": [r'bahasa', r'linguistik', r'language', r'linguistic'],
        "identity": [r'identitas', r'jati diri', r'identity', r'self'],
        "colonialism": [r'kolonial', r'penjajah', r'colonial', r'imperialism'],
        "resistance": [r'perlawanan', r'resistensi', r'resistance', r'opposition'],
    }
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize discourse chunker.
        
        Args:
            chunk_size: Target size for chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Fallback to basic splitter for non-semantic splitting
        self.basic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
    
    def semantic_split(self, text: str) -> List[str]:
        """Split text by semantic boundaries (paragraphs, arguments).
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks split by semantic boundaries
        """
        # Primary split: paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding paragraph would exceed chunk size, start new chunk
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                current_chunk = para
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If no semantic splits possible, fallback to basic splitter
        if not chunks:
            chunks = self.basic_splitter.split_text(text)
        
        return chunks
    
    def classify_chunk_role(self, chunk_text: str) -> ChunkRole:
        """Classify the argumentative/discourse role of a chunk.
        
        Args:
            chunk_text: Text to classify
            
        Returns:
            Chunk role classification
        """
        text_lower = chunk_text.lower()
        
        # Check for question patterns
        if any(re.search(pattern, text_lower) for pattern in self.QUESTION_PATTERNS):
            return "question"
        
        # Check for definition patterns
        if any(re.search(pattern, text_lower) for pattern in self.DEFINITION_PATTERNS):
            return "definition"
        
        # Check for example patterns
        if any(re.search(pattern, text_lower) for pattern in self.EXAMPLE_PATTERNS):
            return "example"
        
        # Check for counter-argument patterns
        if any(re.search(pattern, text_lower) for pattern in self.COUNTER_PATTERNS):
            return "counter_argument"
        
        # Check for argument patterns
        if any(re.search(pattern, text_lower) for pattern in self.ARGUMENT_PATTERNS):
            return "argument"
        
        # Check if it's narrative (contains storytelling elements)
        # Simple heuristic: presence of past tense verbs, temporal markers
        narrative_markers = [r'\btelah\b', r'\bpernah\b', r'\bdahulu\b', r'\bhistory\b']
        if any(re.search(pattern, text_lower) for pattern in narrative_markers):
            return "narrative"
        
        return "unknown"
    
    def detect_discourse_position(self, chunk_text: str, chunk_role: ChunkRole) -> DiscoursePosition:
        """Detect the discourse position/stance of the chunk.
        
        Args:
            chunk_text: Text to analyze
            chunk_role: Already classified role
            
        Returns:
            Discourse position
        """
        text_lower = chunk_text.lower()
        
        # Counter-arguments are typically critical
        if chunk_role == "counter_argument":
            return "critical"
        
        # Questions are questioning
        if chunk_role == "question":
            return "questioning"
        
        # Look for critical language
        critical_markers = [
            r'masalah', r'kritik', r'problem', r'issue', r'concern',
            r'tidak', r'bukan', r'not', r'never'
        ]
        critical_count = sum(1 for pattern in critical_markers if re.search(pattern, text_lower))
        
        # Look for supportive language
        supportive_markers = [
            r'mendukung', r'setuju', r'positif', r'support', r'agree',
            r'baik', r'good', r'beneficial'
        ]
        supportive_count = sum(1 for pattern in supportive_markers if re.search(pattern, text_lower))
        
        if critical_count > supportive_count:
            return "critical"
        elif supportive_count > critical_count:
            return "supportive"
        
        return "neutral"
    
    def extract_themes(self, chunk_text: str) -> List[str]:
        """Extract thematic tags from chunk.
        
        Args:
            chunk_text: Text to analyze
            
        Returns:
            List of detected theme tags
        """
        text_lower = chunk_text.lower()
        detected_themes = []
        
        for theme, patterns in self.THEME_KEYWORDS.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                detected_themes.append(theme)
        
        return detected_themes
    
    def detect_citation(self, chunk_text: str) -> bool:
        """Detect if chunk contains citations or references.
        
        Args:
            chunk_text: Text to check
            
        Returns:
            True if citations detected
        """
        citation_patterns = [
            r'\(\d{4}\)',  # Year citations like (2023)
            r'\[\d+\]',    # Reference numbers like [1]
            r'et al\.',    # Academic citations
            r'ibid',       # Latin reference markers
        ]
        
        return any(re.search(pattern, chunk_text) for pattern in citation_patterns)
    
    def chunk_with_discourse(
        self, 
        documents: List[Document],
        curatorial_metadata: Optional[Dict] = None
    ) -> List[Document]:
        """Main chunking function with discourse awareness.
        
        Args:
            documents: Documents to chunk
            curatorial_metadata: Optional curatorial metadata to preserve
            
        Returns:
            List of discourse-aware chunks
        """
        result_chunks = []
        
        for doc in documents:
            # Semantic split
            text_chunks = self.semantic_split(doc.page_content)
            
            for i, chunk_text in enumerate(text_chunks):
                # Classify discourse metadata
                chunk_role = self.classify_chunk_role(chunk_text)
                discourse_position = self.detect_discourse_position(chunk_text, chunk_role)
                themes = self.extract_themes(chunk_text)
                has_citation = self.detect_citation(chunk_text)
                
                # Create discourse metadata
                discourse_meta = DiscourseMetadata(
                    chunk_role=chunk_role,
                    discourse_position=discourse_position,
                    themes=themes,
                    has_citation=has_citation
                )
                
                # Merge with document metadata
                chunk_metadata = doc.metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "chunk_role": discourse_meta.chunk_role,
                    "discourse_position": discourse_meta.discourse_position,
                    "themes": discourse_meta.themes,
                    "has_citation": discourse_meta.has_citation,
                })
                
                # Add curatorial metadata if provided
                if curatorial_metadata:
                    chunk_metadata.update(curatorial_metadata)
                
                # Create chunk document
                chunk_doc = Document(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                )
                
                result_chunks.append(chunk_doc)
        
        return result_chunks


def get_discourse_chunker(
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> DiscourseAwareChunker:
    """Factory function to get discourse chunker.
    
    Args:
        chunk_size: Optional custom chunk size
        chunk_overlap: Optional custom overlap
        
    Returns:
        DiscourseAwareChunker instance
    """
    settings = get_settings()
    
    return DiscourseAwareChunker(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP
    )
