"""Knowledge Store - SQLite-based metadata and relation storage.

This is the second half of the dual storage system. While ChromaDB stores
vectors for similarity search, this store maintains rich metadata, relations,
and cultural context for epistemic filtering and non-hegemonic retrieval.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

from app.config import get_settings


class KnowledgeStore:
    """SQLite-based knowledge store for metadata and relations."""
    
    def __init__(self, db_path: str = "./data/cultural_knowledge.db"):
        """Initialize knowledge store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.
        
        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    
    def _init_schema(self):
        """Initialize database schema with all tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Documents table - main document metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vector_id TEXT UNIQUE NOT NULL,
                title TEXT,
                source_type TEXT NOT NULL,
                authority_level TEXT NOT NULL,
                epistemic_origin TEXT NOT NULL,
                language TEXT DEFAULT 'id',
                region TEXT DEFAULT 'nusantara',
                discourse_position TEXT DEFAULT 'neutral',
                chunk_role TEXT DEFAULT 'unknown',
                sensitivity TEXT DEFAULT 'standard',
                ingest_policy TEXT DEFAULT 'cultural',
                folder_path TEXT,
                filename TEXT,
                chunk_index INTEGER,
                has_citation BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # Metadata table - flexible key-value for additional metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        
        # Themes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # Document-Theme mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_themes (
                doc_id INTEGER NOT NULL,
                theme_id INTEGER NOT NULL,
                PRIMARY KEY (doc_id, theme_id),
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        
        # Relations table - document relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_doc_id INTEGER NOT NULL,
                to_doc_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (from_doc_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (to_doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        
        # Embedding versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embedding_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                model TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
        
        # Create indices for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vector_id ON documents(vector_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON documents(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authority ON documents(authority_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic ON documents(epistemic_origin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_language ON documents(language)")
        
        conn.commit()
        conn.close()
    
    def add_document(
        self,
        vector_id: str,
        metadata: Dict[str, Any]
    ) -> int:
        """Add document with metadata to knowledge store.
        
        Args:
            vector_id: ID from vector store (ChromaDB)
            metadata: Full metadata dictionary
            
        Returns:
            Document ID in knowledge store
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Extract main fields
        doc_data = {
            "vector_id": vector_id,
            "title": metadata.get("title", "Untitled"),
            "source_type": metadata.get("source_type", "general"),
            "authority_level": metadata.get("authority_level", "situated"),
            "epistemic_origin": metadata.get("epistemic_origin", "local_knowledge"),
            "language": metadata.get("language", "id"),
            "region": metadata.get("region", "nusantara"),
            "discourse_position": metadata.get("discourse_position", "neutral"),
            "chunk_role": metadata.get("chunk_role", "unknown"),
            "sensitivity": metadata.get("sensitivity", "standard"),
            "ingest_policy": metadata.get("ingest_policy", "cultural"),
            "folder_path": metadata.get("folder_path"),
            "filename": metadata.get("filename"),
            "chunk_index": metadata.get("chunk_index"),
            "has_citation": 1 if metadata.get("has_citation", False) else 0,
            "created_at": metadata.get("ingested_at", datetime.utcnow().isoformat()),
        }
        
        # Insert document
        cursor.execute("""
            INSERT INTO documents (
                vector_id, title, source_type, authority_level, epistemic_origin,
                language, region, discourse_position, chunk_role, sensitivity,
                ingest_policy, folder_path, filename, chunk_index, has_citation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(doc_data.values()))
        
        doc_id = cursor.lastrowid
        
        # Add themes
        themes = metadata.get("themes", [])
        if isinstance(themes, str):
            themes = json.loads(themes)
        
        for theme_name in themes:
            theme_id = self._get_or_create_theme(cursor, theme_name)
            cursor.execute("""
                INSERT OR IGNORE INTO document_themes (doc_id, theme_id)
                VALUES (?, ?)
            """, (doc_id, theme_id))
        
        # Add embedding version
        if "embedding_model" in metadata and "embedding_version" in metadata:
            cursor.execute("""
                INSERT INTO embedding_versions (doc_id, model, version, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                doc_id,
                metadata["embedding_model"],
                metadata["embedding_version"],
                metadata.get("embedding_created_at", datetime.utcnow().isoformat())
            ))
        
        # Store additional metadata in key-value table
        excluded_keys = set(doc_data.keys()) | {"themes", "embedding_model", "embedding_version"}
        for key, value in metadata.items():
            if key not in excluded_keys and value is not None:
                cursor.execute("""
                    INSERT INTO metadata (doc_id, key, value)
                    VALUES (?, ?, ?)
                """, (doc_id, key, str(value)))
        
        conn.commit()
        conn.close()
        
        return doc_id
    
    def _get_or_create_theme(self, cursor, theme_name: str) -> int:
        """Get or create theme ID.
        
        Args:
            cursor: Database cursor
            theme_name: Theme name
            
        Returns:
            Theme ID
        """
        cursor.execute("SELECT id FROM themes WHERE name = ?", (theme_name,))
        row = cursor.fetchone()
        
        if row:
            return row[0]
        
        cursor.execute("INSERT INTO themes (name) VALUES (?)", (theme_name,))
        return cursor.lastrowid
    
    def get_document_by_vector_id(self, vector_id: str) -> Optional[Dict]:
        """Get document metadata by vector ID.
        
        Args:
            vector_id: Vector store ID
            
        Returns:
            Document metadata or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE vector_id = ?", (vector_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        doc = dict(row)
        doc_id = doc['id']
        
        # Get themes
        cursor.execute("""
            SELECT t.name FROM themes t
            JOIN document_themes dt ON t.id = dt.theme_id
            WHERE dt.doc_id = ?
        """, (doc_id,))
        doc['themes'] = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return doc
    
    def add_relation(
        self,
        from_vector_id: str,
        to_vector_id: str,
        relation_type: str
    ) -> bool:
        """Create relation between documents.
        
        Args:
            from_vector_id: Source document vector ID
            to_vector_id: Target document vector ID
            relation_type: Type of relation (e.g., 'cites', 'responds_to', 'similar_to')
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get document IDs
        cursor.execute("SELECT id FROM documents WHERE vector_id = ?", (from_vector_id,))
        from_row = cursor.fetchone()
        
        cursor.execute("SELECT id FROM documents WHERE vector_id = ?", (to_vector_id,))
        to_row = cursor.fetchone()
        
        if not from_row or not to_row:
            conn.close()
            return False
        
        # Create relation
        cursor.execute("""
            INSERT INTO relations (from_doc_id, to_doc_id, relation_type, created_at)
            VALUES (?, ?, ?, ?)
        """, (from_row[0], to_row[0], relation_type, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    def query_by_filters(
        self,
        source_type: Optional[str] = None,
        authority_level: Optional[str] = None,
        epistemic_origin: Optional[str] = None,
        themes: Optional[List[str]] = None,
        language: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """Query documents by cultural/epistemic filters.
        
        Args:
            source_type: Filter by source type
            authority_level: Filter by authority level
            epistemic_origin: Filter by epistemic origin
            themes: Filter by themes (AND logic)
            language: Filter by language
            limit: Maximum results
            
        Returns:
            List of vector IDs matching filters
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query
        where_clauses = []
        params = []
        
        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        
        if authority_level:
            where_clauses.append("authority_level = ?")
            params.append(authority_level)
        
        if epistemic_origin:
            where_clauses.append("epistemic_origin = ?")
            params.append(epistemic_origin)
        
        if language:
            where_clauses.append("language = ?")
            params.append(language)
        
        # Base query
        if themes:
            # Query with theme filtering
            theme_placeholders = ",".join(["?"] * len(themes))
            query = f"""
                SELECT d.vector_id FROM documents d
                JOIN document_themes dt ON d.id = dt.doc_id
                JOIN themes t ON dt.theme_id = t.id
                WHERE t.name IN ({theme_placeholders})
            """
            params.extend(themes)
            
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)
            
            query += f" GROUP BY d.id HAVING COUNT(DISTINCT t.id) = ? LIMIT ?"
            params.extend([len(themes), limit])
        else:
            query = "SELECT vector_id FROM documents"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        results = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict:
        """Get knowledge store statistics.
        
        Returns:
            Statistics dictionary
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        stats['total_documents'] = cursor.fetchone()[0]
        
        # By source type
        cursor.execute("""
            SELECT source_type, COUNT(*) as count
            FROM documents
            GROUP BY source_type
        """)
        stats['by_source_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By authority level
        cursor.execute("""
            SELECT authority_level, COUNT(*) as count
            FROM documents
            GROUP BY authority_level
        """)
        stats['by_authority'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total themes
        cursor.execute("SELECT COUNT(*) FROM themes")
        stats['total_themes'] = cursor.fetchone()[0]
        
        # Total relations
        cursor.execute("SELECT COUNT(*) FROM relations")
        stats['total_relations'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


# Global instance
_knowledge_store: Optional[KnowledgeStore] = None


def get_knowledge_store() -> KnowledgeStore:
    """Get or create knowledge store instance.
    
    Returns:
        KnowledgeStore instance
    """
    global _knowledge_store
    
    if _knowledge_store is None:
        settings = get_settings()
        db_path = getattr(settings, 'KNOWLEDGE_STORE_PATH', './data/cultural_knowledge.db')
        _knowledge_store = KnowledgeStore(db_path=db_path)
    
    return _knowledge_store
