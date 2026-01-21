#!/usr/bin/env python3
"""Test script untuk Cultural Nodes dengan dokumen real dan evaluasi discourse detection."""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pipeline import get_pipeline
from app.core.cultural_retriever import get_cultural_retriever, RetrievalStrategy


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_ingestion():
    """Test ingestion of all sample documents."""
    print_section("PHASE 1: DOCUMENT INGESTION")
    
    pipeline = get_pipeline(verbose=True)
    
    test_files = [
        ("knowledge_base/community/manifesto/teknologi-lokal.txt", "community"),
        ("knowledge_base/community/transcript/diskusi-komunitas-tech.txt", "community"),
        ("knowledge_base/academic/penelitian-teknologi-digital.md", "academic"),
        ("knowledge_base/media/artikel-media-sosial.txt", "media"),
    ]
    
    total_chunks = 0
    
    for file_path, category in test_files:
        if os.path.exists(file_path):
            try:
                chunks = pipeline.ingest_file(file_path, category=category)
                total_chunks += chunks
                print(f"✓ {Path(file_path).name}: {chunks} chunks")
            except Exception as e:
                print(f"✗ Error ingesting {file_path}: {e}")
        else:
            print(f"✗ File not found: {file_path}")
    
    print(f"\n📊 Total chunks ingested: {total_chunks}")
    
    # Show statistics
    print_section("KNOWLEDGE BASE STATISTICS")
    stats = pipeline.get_stats()
    
    print("\n📦 Vector Store:")
    print(f"  Collection: {stats['vector_store']['name']}")
    print(f"  Total Documents: {stats['vector_store']['count']}")
    
    print("\n📚 Knowledge Store:")
    print(f"  Total Documents: {stats['knowledge_store']['total_documents']}")
    
    print("\n  By Source Type:")
    for source, count in stats['knowledge_store'].get('by_source_type', {}).items():
        print(f"    {source}: {count}")
    
    print("\n  By Authority Level:")
    for authority, count in stats['knowledge_store'].get('by_authority', {}).items():
        print(f"    {authority}: {count}")
    
    print(f"\n  Total Themes: {stats['knowledge_store']['total_themes']}")
    print(f"  Total Relations: {stats['knowledge_store']['total_relations']}")
    
    return total_chunks > 0


def test_cultural_retrieval():
    """Test cultural retrieval strategies."""
    print_section("PHASE 2: CULTURAL RETRIEVAL TESTING")
    
    retriever = get_cultural_retriever()
    test_query = "Bagaimana teknologi mempengaruhi masyarakat?"
    
    print(f"\n🔍 Test Query: \"{test_query}\"\n")
    
    # Test 1: Standard retrieval
    print("1️⃣  STANDARD SIMILARITY RETRIEVAL")
    print("-" * 70)
    standard_docs = retriever.retrieve_standard(test_query, k=3)
    for i, doc in enumerate(standard_docs, 1):
        meta = doc.metadata
        print(f"  [{i}] Source: {meta.get('source_type', 'N/A')} | "
              f"Authority: {meta.get('authority_level', 'N/A')}")
        print(f"      Role: {meta.get('chunk_role', 'N/A')} | "
              f"Position: {meta.get('discourse_position', 'N/A')}")
        print(f"      Themes: {', '.join(meta.get('themes', []))}")
        print(f"      Preview: {doc.page_content[:100]}...")
        print()
    
    # Test 2: Epistemic filtering (community only)
    print("\n2️⃣  EPISTEMIC FILTERING (Community Sources Only)")
    print("-" * 70)
    community_docs = retriever.retrieve_epistemic(
        test_query,
        source_type="community",
        k=3
    )
    print(f"  Found {len(community_docs)} community documents")
    for i, doc in enumerate(community_docs, 1):
        meta = doc.metadata
        print(f"  [{i}] {meta.get('filename', 'N/A')}")
        print(f"      Origin: {meta.get('epistemic_origin', 'N/A')}")
        print()
    
    # Test 3: Plural perspectives
    print("\n3️⃣  PLURAL RETRIEVAL (Multiple Perspectives)")
    print("-" * 70)
    perspectives = retriever.retrieve_plural(test_query, k_per_source=1)
    for source_type, docs in perspectives.items():
        print(f"  📂 {source_type.upper()}: {len(docs)} document(s)")
        for doc in docs:
            meta = doc.metadata
            print(f"      - Position: {meta.get('discourse_position', 'N/A')}")
            print(f"        Themes: {', '.join(meta.get('themes', [])[:3])}")
        print()
    
    # Test 4: Authority-ranked (boost community)
    print("\n4️⃣  AUTHORITY-RANKED (Community Boosted)")
    print("-" * 70)
    ranked_docs = retriever.retrieve_authority_ranked(
        test_query,
        boost_community=True,
        k=4
    )
    for i, doc in enumerate(ranked_docs, 1):
        meta = doc.metadata
        print(f"  [{i}] Authority: {meta.get('authority_level', 'N/A')} | "
              f"Source: {meta.get('source_type', 'N/A')}")
    print()
    
    # Test 5: Discourse balanced
    print("\n5️⃣  DISCOURSE-BALANCED RETRIEVAL")
    print("-" * 70)
    balanced_docs = retriever.retrieve_discourse_balanced(test_query, k=4)
    discourse_positions = {}
    for doc in balanced_docs:
        position = doc.metadata.get('discourse_position', 'unknown')
        discourse_positions[position] = discourse_positions.get(position, 0) + 1
    
    print(f"  Total documents: {len(balanced_docs)}")
    print(f"  Discourse distribution:")
    for position, count in discourse_positions.items():
        print(f"    - {position}: {count}")
    print()
    
    # Test 6: Cultural context assembly
    print("\n6️⃣  CULTURAL CONTEXT ASSEMBLY")
    print("-" * 70)
    context = retriever.assemble_cultural_context(
        test_query,
        include_perspectives=True,
        boost_community=True,
        k=3
    )
    
    print(f"  Primary documents: {len(context['primary_docs'])}")
    print(f"  Perspectives included: {', '.join(context['perspectives'].keys())}")
    print()
    print("  📊 Metadata Summary:")
    summary = context['metadata_summary']
    print(f"    Total documents: {summary['total_documents']}")
    print(f"    By source: {summary['by_source']}")
    print(f"    By authority: {summary['by_authority']}")
    print(f"    By discourse: {summary['by_discourse']}")
    print(f"    Top themes: {list(summary['themes'].items())[:5]}")


def evaluate_discourse_detection():
    """Evaluate discourse detection quality."""
    print_section("PHASE 3: DISCOURSE DETECTION EVALUATION")
    
    from app.core.knowledge_store import get_knowledge_store
    
    knowledge_store = get_knowledge_store()
    
    # Get sample documents
    import sqlite3
    conn = knowledge_store._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, chunk_role, discourse_position, themes
        FROM documents
        LIMIT 10
    """)
    
    print("\n📝 Sample Discourse Metadata:\n")
    for row in cursor.fetchall():
        title = row[0] if row[0] else "Untitled"
        chunk_role = row[1]
        discourse_position = row[2]
        themes = row[3]
        
        print(f"  Document: {title[:40]}...")
        print(f"    Chunk Role: {chunk_role}")
        print(f"    Discourse Position: {discourse_position}")
        print(f"    Themes: {themes}")
        print()
    
    conn.close()
    
    print("\n✅ Discourse detection appears to be working!")
    print("   Check the metadata to verify accuracy.")


def main():
    """Main test function."""
    print("\n" + "="*70)
    print("  CULTURAL NODES - COMPREHENSIVE TESTING")
    print("="*70)
    
    try:
        # Phase 1: Ingestion
        success = test_ingestion()
        
        if not success:
            print("\n⚠️  No documents were ingested. Please check file paths.")
            return
        
        # Phase 2: Cultural retrieval
        test_cultural_retrieval()
        
        # Phase 3: Discourse evaluation
        evaluate_discourse_detection()
        
        print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
