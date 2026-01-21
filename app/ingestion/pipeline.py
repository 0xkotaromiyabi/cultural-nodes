"""Document ingestion pipeline with Cultural Nodes architecture.

This pipeline implements epistemic awareness through:
1. Curatorial Gate - Extract source provenance and authority
2. Discourse Chunking - Semantic chunks with argumentative roles
3. Metadata Enrichment - Rich cultural and epistemic metadata
4. Embedding Versioning - Track model versions
5. Dual Storage - Vector store + Knowledge store
"""

from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

from app.ingestion.loaders import load_directory, load_url, load_pdf, load_text, load_markdown
from app.ingestion.curator import get_curator
from app.ingestion.discourse_chunker import get_discourse_chunker
from app.ingestion.chunker import chunk_documents  # Fallback
from app.core.metadata import get_metadata_enricher
from app.core.embedding_version import get_current_embedding_metadata
from app.core.vectorstore import add_documents, get_collection_stats
from app.core.knowledge_store import get_knowledge_store
from app.config import get_settings


class IngestionPipeline:
    """Culturally-aware ingestion pipeline.
    
    Pipeline flow:
    knowledge_base/* → [Curatorial Gate] → [Parser] → [Discourse Chunker] 
    → [Metadata Enrichment] → [Embedding (versioned)] → [Dual Storage]
    """
    
    def __init__(self, verbose: bool = True):
        """Initialize pipeline.
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        self.settings = get_settings()
        
        # Initialize components
        self.curator = get_curator(knowledge_base_root="./knowledge_base")
        self.discourse_chunker = get_discourse_chunker()
        self.metadata_enricher = get_metadata_enricher()
        self.knowledge_store = get_knowledge_store()
    
    def _log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _apply_curatorial_gate(
        self,
        documents: List[Document],
        file_path: str
    ) -> List[Document]:
        """Apply curatorial gate to extract epistemic metadata.
        
        Args:
            documents: Documents to curate
            file_path: Original file path
            
        Returns:
            Documents enriched with curatorial metadata
        """
        self._log("[CURATE] Applying curatorial gate...")
        
        # Extract curatorial metadata from path and content
        sample_content = documents[0].page_content[:1000] if documents else ""
        curatorial_meta = self.curator.curate_document(
            file_path=file_path,
            content=sample_content
        )
        
        # Add to all documents
        curatorial_dict = curatorial_meta.dict()
        for doc in documents:
            doc.metadata.update(curatorial_dict)
        
        self._log(f"    Source: {curatorial_meta.source_type}")
        self._log(f"    Authority: {curatorial_meta.authority_level.value}")
        self._log(f"    Origin: {curatorial_meta.epistemic_origin.value}")
        
        return documents
    
    def _chunk_documents(
        self,
        documents: List[Document],
        use_discourse: bool = True
    ) -> List[Document]:
        """Chunk documents with discourse awareness.
        
        Args:
            documents: Documents to chunk
            use_discourse: Whether to use discourse chunker
            
        Returns:
            Chunked documents with discourse metadata
        """
        if use_discourse and self.settings.USE_DISCOURSE_CHUNKING:
            self._log("[CHUNK] Discourse-aware chunking...")
            
            # Extract curatorial metadata to pass along
            curatorial_meta = {}
            if documents:
                curatorial_meta = {
                    k: v for k, v in documents[0].metadata.items()
                    if k in ['source_type', 'authority_level', 'epistemic_origin', 
                            'language', 'region', 'ingest_policy', 'folder_path']
                }
            
            chunks = self.discourse_chunker.chunk_with_discourse(
                documents,
                curatorial_metadata=curatorial_meta
            )
        else:
            self._log("[CHUNK] Basic chunking...")
            chunks = chunk_documents(documents)
        
        return chunks
    
    def _enrich_metadata(self, chunks: List[Document]) -> List[Document]:
        """Enrich chunks with complete metadata.
        
        Args:
            chunks: Chunks to enrich
            
        Returns:
            Enriched chunks
        """
        self._log("[ENRICH] Enriching metadata...")
        
        # Add embedding version to all chunks
        embedding_meta = get_current_embedding_metadata()
        
        for chunk in chunks:
            # Enrich with all metadata sources
            enriched_meta = self.metadata_enricher.enrich_metadata(
                base_metadata=chunk.metadata,
                content=chunk.page_content
            )
            
            # Add embedding version
            enriched_meta.update(embedding_meta)
            
            # Update chunk metadata
            chunk.metadata = enriched_meta
        
        return chunks
    
    def _store_dual(self, chunks: List[Document]) -> List[str]:
        """Store in dual system: Vector store + Knowledge store.
        
        Args:
            chunks: Chunks to store
            
        Returns:
            List of vector IDs
        """
        self._log(f"[STORE] Dual storage: {len(chunks)} chunks...")
        
        # Store in vector store (ChromaDB)
        vector_ids = add_documents(chunks)
        
        # Store in knowledge store (SQLite)
        for vector_id, chunk in zip(vector_ids, chunks):
            try:
                self.knowledge_store.add_document(
                    vector_id=vector_id,
                    metadata=chunk.metadata
                )
            except Exception as e:
                self._log(f"    [WARN] Knowledge store error for {vector_id}: {e}")
        
        return vector_ids
    
    def ingest_file(self, file_path: str, category: str = "general") -> int:
        """Ingest a single file with full Cultural Nodes pipeline.
        
        Args:
            file_path: Path to the file
            category: Category tag for the document
            
        Returns:
            Number of chunks ingested
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        
        self._log(f"\n[FILE] Ingesting: {path.name}")
        self._log("="*60)
        
        # 1. LOAD
        self._log("[LOAD] Loading document...")
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
            doc.metadata["title"] = doc.metadata.get("filename", path.stem)
        
        # 2. CURATORIAL GATE
        documents = self._apply_curatorial_gate(documents, file_path)
        
        # 3. DISCOURSE CHUNKING
        chunks = self._chunk_documents(documents)
        
        # 4. METADATA ENRICHMENT
        chunks = self._enrich_metadata(chunks)
        
        # 5. DUAL STORAGE
        vector_ids = self._store_dual(chunks)
        
        self._log(f"\n[DONE] {path.name}: {len(chunks)} chunks stored")
        self._log("="*60)
        
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
        self._log(f"\n[DIR] Scanning directory: {directory_path}")
        self._log("="*60)
        
        # Load all documents
        documents = load_directory(directory_path, recursive, extensions)
        
        if not documents:
            self._log("[WARN] No documents found")
            return 0
        
        # Group documents by file for curatorial processing
        from collections import defaultdict
        files_docs = defaultdict(list)
        
        for doc in documents:
            file_path = doc.metadata.get("filepath", "unknown")
            files_docs[file_path].append(doc)
        
        total_chunks = 0
        
        # Process each file
        for file_path, docs in files_docs.items():
            try:
                # Add category
                for doc in docs:
                    doc.metadata["category"] = category
                
                # Curatorial gate
                docs = self._apply_curatorial_gate(docs, file_path)
                
                # Chunk
                chunks = self._chunk_documents(docs)
                
                # Enrich
                chunks = self._enrich_metadata(chunks)
                
                # Store
                self._store_dual(chunks)
                
                total_chunks += len(chunks)
                
            except Exception as e:
                self._log(f"[ERROR] Failed to process {file_path}: {e}")
        
        self._log(f"\n[DONE] Directory: {total_chunks} total chunks")
        self._log("="*60)
        
        return total_chunks
    
    def ingest_url(self, url: str, category: str = "web") -> int:
        """Ingest content from a URL.
        
        Args:
            url: Web URL to scrape
            category: Category tag for the content
            
        Returns:
            Number of chunks ingested
        """
        self._log(f"\n[URL] Fetching: {url}")
        self._log("="*60)
        
        documents = load_url(url)
        
        # Add metadata
        for doc in documents:
            doc.metadata["category"] = category
            doc.metadata["title"] = url
        
        # Apply curatorial gate (URLs treated as media by default)
        for doc in documents:
            doc.metadata.update({
                "source_type": "media",
                "authority_level": "media",
                "epistemic_origin": "media_discourse",
                "language": "en",
                "region": "global"
            })
        
        # Chunk, enrich, store
        chunks = self._chunk_documents(documents)
        chunks = self._enrich_metadata(chunks)
        self._store_dual(chunks)
        
        self._log(f"\n[DONE] URL: {len(chunks)} chunks")
        self._log("="*60)
        
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
        self._log(f"\n[TEXT] Processing: {title}")
        self._log("="*60)
        
        from app.ingestion.chunker import chunk_text
        
        # Basic chunking for raw text
        chunks = chunk_text(text, metadata={
            "title": title,
            "category": category,
            "source_type": "text",
            "authority_level": "situated",
            "epistemic_origin": "local_knowledge"
        })
        
        # Enrich and store
        chunks = self._enrich_metadata(chunks)
        self._store_dual(chunks)
        
        self._log(f"\n[DONE] Text: {len(chunks)} chunks")
        self._log("="*60)
        
        return len(chunks)
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics from both stores.
        
        Returns:
            Dictionary with collection stats
        """
        # Vector store stats
        vector_stats = get_collection_stats()
        
        # Knowledge store stats
        knowledge_stats = self.knowledge_store.get_stats()
        
        return {
            "vector_store": vector_stats,
            "knowledge_store": knowledge_stats
        }


def get_pipeline(verbose: bool = True) -> IngestionPipeline:
    """Factory function to get pipeline instance.
    
    Args:
        verbose: Whether to print progress messages
        
    Returns:
        IngestionPipeline instance
    """
    return IngestionPipeline(verbose=verbose)
